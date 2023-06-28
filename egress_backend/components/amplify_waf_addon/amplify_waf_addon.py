import os
from urllib.parse import quote

import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
from aws_cdk import Aws, CfnOutput, CustomResource, Duration
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_route53 as r53
from aws_cdk import aws_route53_targets as r53targets
from aws_cdk import aws_secretsmanager as secrets
from aws_cdk import custom_resources as custom
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime, Tracing
from aws_cdk.aws_logs import RetentionDays
from cdk_nag import NagSuppressions
from constructs import Construct

from ..utils import convert_bool

dirname = os.path.dirname(__file__)


class CustomAmplifyDistribution(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        web_acl_arn: str,
        custom_domain_config: dict,
        app_id: str,
        branch_name: str,
        powertools_layer: LayerVersion,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        amplify_username = secrets.Secret(
            self,
            "rAmplifyUsername",
            description=f"Username created for Amplify app with id {app_id}",
            generate_secret_string=secrets.SecretStringGenerator(
                password_length=12, exclude_punctuation=True
            ),
        )

        amplify_password = secrets.Secret(
            self,
            "rAmplifyPassword",
            description=f"Password created for Amplify app with id {app_id}",
            generate_secret_string=secrets.SecretStringGenerator(
                password_length=32, exclude_characters=":"
            ),
        )

        # Lambda Baic Execution Permissions
        lambda_exec_policy = iam.ManagedPolicy.from_managed_policy_arn(
            self,
            "lambda-exec-policy-00",
            managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        )

        # Amplify Credential Retrieval Lambda Execution Role
        amplify_credentials_retrieval_function_role = iam.Role(
            self,
            "rAmplifyCredentialsRetrievalFunctionRole",
            description="Role used by amplify_credentials_retrieval_function lambda function",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        # Restricts ability to read secret value only to the IAM role used by custom function
        amplify_username.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                resources=[
                    amplify_username.secret_full_arn,
                ],
                actions=[
                    "secretsmanager:GetSecretValue",
                ],
                conditions={
                    "ArnNotEquals": {
                        "aws:PrincipalArn": amplify_credentials_retrieval_function_role.role_arn
                    }
                },
            )
        )
        # Restricts ability to read secret value only to the IAM role used by custom function
        amplify_password.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                resources=[
                    amplify_password.secret_full_arn,
                ],
                actions=[
                    "secretsmanager:GetSecretValue",
                ],
                conditions={
                    "ArnNotEquals": {
                        "aws:PrincipalArn": amplify_credentials_retrieval_function_role.role_arn
                    }
                },
            )
        )

        amplify_credentials_retrieval_function_role.add_managed_policy(
            lambda_exec_policy
        )

        amplify_password.grant_read(amplify_credentials_retrieval_function_role)
        amplify_username.grant_read(amplify_credentials_retrieval_function_role)

        # Function to retrieve base64 encoded authorisation string
        amplify_credentials_retrieval_function = Function(
            self,
            "rAmplifyCredentialsRetrievalFunction",
            description="custom function to retrieve value of scecrets that contain amplify auth info",  # noqa 501
            runtime=Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=Code.from_asset(
                path=os.path.join(dirname, "../../lambda/password_retrieval")
            ),
            timeout=Duration.seconds(30),
            memory_size=128,
            layers=[powertools_layer],
            role=amplify_credentials_retrieval_function_role,
            tracing=Tracing.ACTIVE,
            log_retention=RetentionDays.SIX_MONTHS,
            environment={
                "USERNAME_SECRET_ARN": amplify_username.secret_full_arn,
                "CREDENTIALS_SECRET_ARN": amplify_password.secret_full_arn,
            },
        )

        password_provider = custom.Provider(
            self,
            "rPasswordProvider",
            on_event_handler=amplify_credentials_retrieval_function,
        )

        amplify_auth_value = CustomResource(
            self,
            "rPasswordRequestResource",
            service_token=password_provider.service_token,
            properties={},
        )

        app_branch_update = custom.AwsCustomResource(
            self,
            "rAmplifyAppBranchUpdate",
            policy=custom.AwsCustomResourcePolicy.from_sdk_calls(
                resources=[
                    f"arn:aws:amplify:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{app_id}/branches/{quote(branch_name, safe='')}",
                ]
            ),
            on_create=custom.AwsSdkCall(
                service="Amplify",
                action="updateBranch",
                parameters={
                    "appId": app_id,
                    "branchName": branch_name,
                    "enableBasicAuth": True,
                    "basicAuthCredentials": amplify_auth_value.get_att_string(
                        "EncodedCredentials"
                    ),
                },
                physical_resource_id=custom.PhysicalResourceId.of(
                    "amplify-branch-update"
                ),
            ),
            on_update=custom.AwsSdkCall(
                service="Amplify",
                action="updateBranch",
                parameters={
                    "appId": app_id,
                    "branchName": branch_name,
                    "enableBasicAuth": True,
                    "basicAuthCredentials": amplify_auth_value.get_att_string(
                        "EncodedCredentials"
                    ),
                },
                physical_resource_id=custom.PhysicalResourceId.of(
                    "amplify-branch-update"
                ),
            ),
        )

        app_branch_update.node.add_dependency(amplify_auth_value)
        app_branch_update.node.add_dependency(amplify_auth_value)

        # Format amplify branch
        formatted_amplify_branch = branch_name.replace("/", "-")

        # Define cloudfront distribution
        amplify_app_distribution = cloudfront.Distribution(
            self,
            "rCustomCloudFrontDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    domain_name=f"{formatted_amplify_branch}.{app_id}.amplifyapp.com",
                    custom_headers={
                        "Authorization": amplify_auth_value.get_att_string(
                            "EncodedSuffix"
                        )
                    },
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
            web_acl_id=web_acl_arn,
        )

        if convert_bool(custom_domain_config.get("is_enabled"), bool):
            amplify_app_distribution.node.default_child.add_property_override(
                "DistributionConfig.ViewerCertificate.AcmCertificateArn",
                custom_domain_config.get("cert_arn"),
            )
            amplify_app_distribution.node.default_child.add_property_override(
                "DistributionConfig.ViewerCertificate.SslSupportMethod", "sni-only"
            )
            amplify_app_distribution.node.default_child.add_property_override(
                "DistributionConfig.ViewerCertificate.MinimumProtocolVersion",
                "TLSv1.2_2021",
            )
            amplify_app_distribution.node.default_child.add_property_override(
                "DistributionConfig.Aliases", [custom_domain_config.get("domain_name")]
            )
            hosted_zone = r53.HostedZone.from_hosted_zone_attributes(
                self,
                "rHostedZone",
                hosted_zone_id=custom_domain_config.get("hosted_zone_id"),
                zone_name=custom_domain_config.get("hosted_zone_name"),
            )
            r53.ARecord(
                self,
                "rEgressAppAlias",
                zone=hosted_zone,
                target=r53.RecordTarget.from_alias(
                    r53targets.CloudFrontTarget(amplify_app_distribution)
                ),
                record_name=custom_domain_config.get("domain_name"),
            )

        amplify_app_distribution.node.add_dependency(amplify_auth_value)

        self.amplify_app_distribution = amplify_app_distribution

        # CloudFront cache invalidation Lambda Execution Role
        cache_invalidation_function_role = iam.Role(
            self,
            "rCacheInvalidationFunctionCustomRole",
            description="Role used by cache_invalidation lambda function",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        cache_invalidation_function_role.add_managed_policy(lambda_exec_policy)

        cache_invalidation_function_custom_policy = iam.ManagedPolicy(
            self,
            "rCacheInvalidationFunctionCustomPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "cloudfront:CreateInvalidation",
                    ],
                    resources=[
                        f"arn:aws:cloudfront::{Aws.ACCOUNT_ID}:distribution/{amplify_app_distribution.distribution_id}"
                    ],
                ),
            ],
        )

        cache_invalidation_function_role.add_managed_policy(
            cache_invalidation_function_custom_policy
        )

        # Function to trigger CloudFront invalidation
        cache_invalidation_function = Function(
            self,
            "rCacheInvalidationFunction",
            description="custom function to trigger cloudfront cache invalidation",  # noqa 501
            runtime=Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=Code.from_asset(
                path=os.path.join(dirname, "../../lambda/cache_invalidation")
            ),
            timeout=Duration.seconds(30),
            memory_size=128,
            layers=[powertools_layer],
            role=cache_invalidation_function_role,
            tracing=Tracing.ACTIVE,
            log_retention=RetentionDays.SIX_MONTHS,
            environment={
                "DISTRIBUTION_ID": amplify_app_distribution.distribution_id,
            },
        )

        events.Rule(
            self,
            "rInvokeCacheInvalidation",
            description="Rule is triggered when the Amplify app is redeployed, which creates a CloudFront cache invalidation request",  # noqa E501
            event_pattern=events.EventPattern(
                source=["aws.amplify"],
                detail_type=["Amplify Deployment Status Change"],
                detail={
                    "appId": [app_id],
                    "branchName": [branch_name],
                    "jobStatus": ["SUCCEED"],
                },
            ),
            targets=[
                targets.LambdaFunction(cache_invalidation_function, retry_attempts=2)
            ],
        )

        CfnOutput(
            self,
            "oCloudFrontDistributionDomain",
            value=amplify_app_distribution.distribution_domain_name,
        )

        # Stack Suppressions
        NagSuppressions.add_resource_suppressions(
            amplify_username,
            suppressions=[
                {
                    "id": "AwsSolutions-SMG4",
                    "reason": "user to retrigger rotation by recreating stack",
                }
            ],
        )

        NagSuppressions.add_resource_suppressions(
            amplify_password,
            suppressions=[
                {
                    "id": "AwsSolutions-SMG4",
                    "reason": "user to retrigger rotation by recreating stack",
                }
            ],
        )

        NagSuppressions.add_resource_suppressions(
            amplify_app_distribution,
            suppressions=[
                {
                    "id": "AwsSolutions-CFR1",
                    "reason": "geo restictions to be enabled using WAF by user",
                },
                {
                    "id": "AwsSolutions-CFR3",
                    "reason": "user to override the logging property as required",
                },
                {
                    "id": "AwsSolutions-CFR4",
                    "reason": "user to override when using a custom domain and certificate",
                },
            ],
        )

        NagSuppressions.add_resource_suppressions(
            cache_invalidation_function_role,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "CDK generated service role and policy",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "CDK generated service role and policy",
                },
                {
                    "id": "AwsSolutions-L1",
                    "reason": "CDK generated custom resource",
                },
            ],
            apply_to_children=True,
        )

        NagSuppressions.add_resource_suppressions(
            password_provider,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "CDK generated service role and policy",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "CDK generated service role and policy",
                },
                {
                    "id": "AwsSolutions-L1",
                    "reason": "CDK generated custom resource",
                },
            ],
            apply_to_children=True,
        )

        NagSuppressions.add_resource_suppressions(
            amplify_credentials_retrieval_function_role,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "CDK generated service role and policy",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "CDK generated service role and policy",
                },
            ],
            apply_to_children=True,
        )
