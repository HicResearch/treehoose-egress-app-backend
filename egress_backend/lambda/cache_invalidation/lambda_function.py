import os
import uuid

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

logger = Logger(service="EgressWebappCacheInvalidation", sample_rate=0.1)

# Setup the client
service_client = boto3.client("cloudfront")


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    try:
        service_client.create_invalidation(
            DistributionId=os.environ["DISTRIBUTION_ID"],
            InvalidationBatch={
                "Paths": {"Quantity": 1, "Items": ["/*"]},
                "CallerReference": str(uuid.uuid4()),
            },
        )

        logger.info("Cache invalidation request submitted successfully")
    except ClientError as e:
        logger.error(e.response["Error"]["Message"])
