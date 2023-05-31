# Egress App Backend

This add-on provides a data egress approval workflow
for researchers to take out data from TRE with the permission of multiple parties
(data manager, research IT, etc.).
The add-on is hosted as a web application supported by
backend infrastructure. Each add-on installation is tied
to a specific TRE project.

The add-on provides a streamlined
process for securely egressing data from the TRE environment
while keeping the TRE admins and Data auditors in complete
control of the process.

All data egress requests and any actions performed on those
are recorded for Audit.

![Egress App Workflow](images/egress-app-workflow.png)

Key Components :

- For the UI: AWS Amplify
- For the backend: AWS Step Functions, Amazon EFS,
  AWS Lambda, Amazon DynamoDB, Amazon SES, Amazon S3, AWS KMS, Amazon SNS, Amazon Cognito, AWS AppSync

## Deployment

**Time to deploy**: Approximately 20 minutes

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using Admin privileges.

- [ ] Download the source code repo using below command and change directory

```console
git clone https://gitlab.aws.dev/aws-wwps-uk-proserve-edu/trusted-research-environment/opensource/secure-egress-backend.git
cd secure-egress-backend
```

- [ ] Edit file _cdk.json_ in the `secure-egress-backend` directory (Step 1C). Change the following required
      parameters for the CDK backend stack:

| Parameter Name                         | Description                                                                                                                                                                                                                                  | Location                                                                                                                                                                                                                                                                              |
| :------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| swb_egress_store_arn                   | Provide resource created in Step 2 - S3 Bucket: Egress Store Bucket Arn                                                                                                                                                                      | Check [AWS CloudFormation](https://eu-west-2.console.aws.amazon.com/cloudformation/home?region=eu-west-2#/) _Resources_ tab for _Stack_ "treprod-ldn-pj1-backend" or go to [Amazon S3 Buckets](https://s3.console.aws.amazon.com/s3/buckets?region=eu-west-2)                         |
| swb_egress_notification_topic          | Provide resource created in Step 2 - SNS Topic: Egress Notification Topic Arn                                                                                                                                                                | Check [AWS CloudFormation](https://eu-west-2.console.aws.amazon.com/cloudformation/home?region=eu-west-2#/) _Resources_ tab for _Stack_ "treprod-ldn-pj1-backend" or go to [Amazon SNS Topics](https://eu-west-2.console.aws.amazon.com/sns/v3/home?region=eu-west-2#/topics)         |
| swb_egress_notification_bucket_arn     | Provide resource created in Step 2 - S3 Bucket: Egress Notification Bucket Arn                                                                                                                                                               | Check [AWS CloudFormation](https://eu-west-2.console.aws.amazon.com/cloudformation/home?region=eu-west-2#/) _Resources_ tab for _Stack_ "treprod-ldn-pj1-backend" or go to [Amazon S3 Buckets](https://s3.console.aws.amazon.com/s3/buckets?region=eu-west-2)                         |
| swb_egress_notification_bucket_kms_arn | Provide resource created in Step 2 - KMS Key: Egress Store Encryption Key Arn                                                                                                                                                                | Check [AWS CloudFormation](https://eu-west-2.console.aws.amazon.com/cloudformation/home?region=eu-west-2#/) _Resources_ tab for _Stack_ "treprod-ldn-pj1-backend" or go to [AWS KMS Keys](https://eu-west-2.console.aws.amazon.com/kms/home?region=eu-west-2#/kms/keys)               |
| swb_egress_store_db_table              | Provide resource created in Step 2 - DynamoDB Table: Egress Store Table Arn                                                                                                                                                                  | Check [AWS CloudFormation](https://eu-west-2.console.aws.amazon.com/cloudformation/home?region=eu-west-2#/) _Resources_ tab for _Stack_ "treprod-ldn-pj1-backend" or go to [Amazon DynamoDB Tables](https://eu-west-2.console.aws.amazon.com/dynamodbv2/home?region=eu-west-2#tables) |
| datalake_target_bucket_arn             | Provide resource created in Step 3 - S3 Bucket: TRE Target Bucket                                                                                                                                                                            | Check [AWS CloudFormation](https://eu-west-2.console.aws.amazon.com/cloudformation/home?region=eu-west-2#/) _Resources_ tab for _Stack_ "TREDataLake1" or go to [Amazon S3 Buckets](https://s3.console.aws.amazon.com/s3/buckets?region=eu-west-2)                                    |
| datalake_target_bucket_kms_arn         | Provide resource created in Step 3 - KMS Key: TRE Target Bucket KMS Key                                                                                                                                                                      | Check [AWS CloudFormation](https://eu-west-2.console.aws.amazon.com/cloudformation/home?region=eu-west-2#/) _Resources_ tab for _Stack_ "TREDataLake1" or go to [AWS KMS Keys](https://eu-west-2.console.aws.amazon.com/kms/home?region=eu-west-2#/kms/keys)                          |
| cognito_userpool_domain                | Provide name for a new Amazon Cognito domain to be created                                                                                                                                                                                   | To view resources created after deployment of this CDK stack, go to service [Amazon Cognito](https://eu-west-2.console.aws.amazon.com/cognito/home?region=eu-west-2)                                                                                                                  |
| max_downloads_allowed                  | The maximum number of downloads allowed for a single egress request                                                                                                                                                                          |                                                                                                                                                                                                                                                                                       |
| download_expiry_seconds                | The validity of the download URL for the egress request in seconds                                                                                                                                                                           |                                                                                                                                                                                                                                                                                       |
| tre_admin_email_address                | Provide a TRE admin email address that will need to be verified after deployment                                                                                                                                                             | To view verified identities after deployment of this CDK stack, go to service [Amazon SES](https://eu-west-2.console.aws.amazon.com/ses/home?region=eu-west-2#/verified-identities)                                                                                                   |
| enable_single_approval                 | Flag that enables just a single stage approval. Accepts string value. Should be set to `"true"` when just one approver needs to approve egress request. Should be set to `"false"` when two approvers are required to approve egress request |                                                                                                                                                                                                                                                                                       |
| ig_workspaces_account                  | Optionally add the account number in which IG lead will spin up a workspace to review egress data. Leave empty to disable (default).                                                                                                         |                                                                                                                                                                                                                                                                                       |
| use_s3_access_points                   | Set to `"true"` if you are using a customised version of ServiceWorkbench with S3 AccessPoints, default `"false"`                                                                                                                            |                                                                                                                                                                                                                                                                                       |

> Note: changing the value for `enable_single_approval` for existing deployment should be done after ensuring there are
> no egress requests in progress.

- [ ] Run the following commands to create an isolated Python environment and deploy the CDK backend stack:

```bash
alias cdkv1="npx aws-cdk@1.154"
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
cdkv1 bootstrap aws://<<AWS_ACCOUNT_ID>>/<<AWS_REGION>> # TRE account ID / eu-west-2
cdkv1 deploy
```

## Solution Overview

- [Egress App Backend](#egress-app-backend)
  - [Deployment](#deployment)
  - [Solution Overview](#solution-overview)
  - [1. Egress Backend Stack](#1-egress-backend-stack)
    - [1.1. Egress Request DynamoDB Table](#11-egress-request-dynamodb-table)
    - [1.2. AppSync API](#12-appsync-api)
    - [1.3. GraphQL Schema Change](#13-graphql-schema-change)
    - [1.4. Egress Staging S3 Bucket](#14-egress-staging-s3-bucket)
    - [1.5. Start Egress Workflow Lambda Function](#15-start-egress-workflow-lambda-function)
    - [1.6. Egress Workflow Step Function](#16-egress-workflow-step-function)

The egress application backend is defined as a Python-based [CDK](https://aws.amazon.com/cdk/) (Cloud Development Kit)
application. The app consists of one stack representing the infrastructure for the egress app backend.

## 1. Egress Backend Stack

The _egress_backend_stack.py_ defines the resources that make up
the egress approval workflow. These include the series of Lambda functions in the StepFunctions
(Egress workflow) and the Amplify app hosting the user interface (Egress Web App).

The egress workflow utilizes [AWS Step Functions](https://aws.amazon.com/step-functions/) which is
a visual workflow service that orchestrates a series of [Lambda](https://aws.amazon.com/lambda/) functions and tasks
that define the data egress approval process.

### 1.1. Egress Request DynamoDB Table

This table is used to store egress requests as they are received from SWB. These requests are shown in the web app
for approval/rejection and all status updates are applied to the entries in this table. The table is encrypted with
a dedicated DynamoDB customer-managed KMS key.

### 1.2. AppSync API

[AWS AppSync](https://aws.amazon.com/appsync/) is a fully managed service that makes it easy to develop GraphQL APIs
by handling the heavy lifting of securely connecting to data sources like DynamoDB, Lambda, and
more. [GraphQL](https://graphql.org/) is a query language for the API, and a server-side runtime for executing
queries using a type system defined for your data.

The data types are defined in _egress_backend/graphql/schema.graphql_
and include the definition of an egress request and its attributes. Additionally, definitions of data queries
and mutations (updates) are also included:

- listRequests - Lists all egress requests (Query)
- updateRequest - Updates a given request with approval status, justification, and approver name (Mutation)
- downloadData - Generates a S3 presigned URL which will be used by the frontend to download data associated with the
  request (Mutation)

Appsync uses the schema in combination with resolvers
(_egress_backend/egress_backend_stack.py_),
which provides integration with a single Lambda (Egress-API) executing the business logic for the API.

The Lambda code is defined in _egress_backend/lambda/egress_api_ where _main.py_
serves as the entry point. This script is called anytime the AppSync endpoint is called and is able to filter
(switch cases) the request type and execute different scripts containing differing business logic.

- **List Requests API**

  - **_Request Parameters:_** None
  - **_Response:_** List of egress request objects
  - Calling the endpoint with the listRequests query will invoke the _list_request.py_ script through _main.py_. This function
    executes a table scan to retrieve all of the egress requests from the DynamoDB table.

- **Update Requests API**

  - **_Request Parameters:_** egress_request_id, workspace_id, download_count
  - **_Response:_** String (Success message)
  - Calling the endpoint with the updatesRequests mutation will invoke the _update_request.py_ script through _main.py_.
    The function starts off by checking if the supplied request_id is valid by querying the database. After successful
    verification of the request, the supplied task token is used to resume the relevant egress workflow (StepFunctions)
    execution passing in an approval or rejection status. The supplied reason is used later in the workflow to update
    the request details in the database.

- **Download Data API**
  - **_Request Parameters:_** egress_request_id, status, download_count
  - **_Response:_** String (S3 presigned URL)
  - Calling the endpoint with the downloadData mutation will invoke the _download_data.py_ script through _main.py_.
    The function first checks if the download*count exceeds a configurable parameter `max_downloads_allowed`
    (specified in \_cdk.json*). If the max download count has not been exceeded, the script proceeds to construct
    the object key from the supplied parameters. If the file exists in the datalake bucket, a S3 presigned URL is
    generated and returned as a string. After successful generation, the download_count attribute for the request is
    updated in the table. Note that the frontend maintains the running total as the user clicks on the button and
    once the limit is reached (by checking the same configurable parameter), the download button is disabled.
    The running total is always sent to the backend with any download requests so that if needed, the database
    table can be updated.

### 1.3. GraphQL Schema Change

> Note: This requires installation of Amplify CLI - instructions can be found [here](https://docs.amplify.aws/cli/start/install)

Any changes to the GraphQL schema should be made inside _egress_backend/graphql/schema.graphql_
in the backend.
This file should then be copied/overwritten to this location _secure-egress-frontend/src/graphql/schema.graphql_
in the client.
Then run the command `amplify add codegen` in _secure-egress-frontend/src/graphql_ to generate the updated models
for the client to use. You should see updated _queries.js_ and _mutations.js_ files in the same location.

### 1.4. Egress Staging S3 Bucket

S3 bucket used to temporarily stage candidate egress objects so they can be inspected by the reviewer(s).
This is an unversioned bucket as it is not designed for long-term storage of data. Once an egress request
has been approved/rejected, its related data in this bucket is deleted immediately. The bucket is encrypted
with a dedicated S3 customer-managed KMS key.

### 1.5. Start Egress Workflow Lambda Function

AWS Lambda function that is subscribed to a SWB-managed SNS topic in order to receive notifications of
new egress requests. This function invokes the step function that defines the egress approval workflow.
It also feeds configuration parameters into the workflow which will
be used at various points. Among the key values are:

- _egress_request_id_: Unique identifier for an egress request.
- _reviewer_list_: List of user groups (as defined in the IdP) that have approval responsibility.
  The list ordering should reflect the approval priority.
- _egress_app_url_: URL for the egress application. Used when sending the final decision
  email to the requester.
- _tre_admin_email_address_: Email address for the TRE administrator(s) or administrator
  group. Also used as the "From" email address for the final decision email. The email body
  also references this email address.

### 1.6. Egress Workflow Step Function

![Egress Workflow](images/Graph-EgressApp-StepFunctions.svg)

- **Save Request To DynamoDB:**

  - Step Function task which uses direct integration with Amazon DynamoDB to write the request
    to the Egress Request DynamoDB table
  - The status of the entry is set to **_PROCESSING_** to maintain consistency with the SWB
    Egress store status update below

- **Update Request in Egress Store DynamoDB (processing):**

  - Step Function task which uses direct integration with Amazon DynamoDB to update the egress
    store item status in the SWB DynamoDB
    table to **_PROCESSING_**
  - With this status in place, the researcher is not permitted to terminate the workspace
    (& associated egress store) because there is a request in flight

- **Copy Objects to Egress Staging:**

  - Step Function task which uses an AWS Lambda function (`copy_egress_candidates_to_staging`) to:
    - Retrieve the JSON version metadata file from the `egress_store_object_list_location` in the
      inbound SNS message. This file contains a list of candidate egress objects and their associated
      S3 Version IDs that relate to this particular egress request. This feature allows the linking between
      an egress request and a specific version of an object in the SWB egress store even if said object
      is modified multiple times
    - Copy the candidate egress objects from the SWB Egress store location to the staging bucket.
      The version ID specified in the JSON file above is specified in the copy command. This is the
      version that will be copied **_even if it is not the current version_** in the source egress
      store bucket
    - Extract a list of distinct file types being staged. This list will be fed into the step
      function so that it can be included in notification alerts

- **Notify Information Governance:**

  - Step Function task which uses direct integration with Amazon SNS to:
    - Publish a notification to the Information Governance SNS topic
    - Format the notification to include:
      - File types
      - Egress Request ID
      - Research Project
      - Researcher Email

- **Information Governance Decision:**

  - Step Function task which uses an AWS Lambda function (`update-egress-request-with-task-token-function`)
    to write a step function task token as an attribute of the egress request item in the DynamoDB table
  - The task pauses and waits for a callback which includes the token before it can resume execution
  - Callback will be received via a GraphQL API call from the frontend which will be processed by the `egress-api-handler`
  - Validation in the API will ensure that only the Information Governance role can update the request at this point in time

- **Save Information Governance Decision:**

  - Step Function task which uses direct integration with Amazon DynamoDB to update the Information Governance decision
    in the DynamoDB table
  - This task is triggered by the UpdateRequest API being invoked. The API invokes a Lambda function which uses
    the task token previously
    retrieved (when requests were loaded in the frontend) to resume the step function execution

- **Information Governance Approved?:**

  - Step Function choice task which parses the status of the request as received from the frontend API call in the
    previous task to determine if the request was **_APPROVED_** or **_REJECTED_** by Information Governance
  - At this step the Step Function also checks if any additional approvals are required based on the value of `is_single_approval_enabled`.
  If no further approvals are required the appropriate data operation is done based on the decision
  and an email is sent to the requester.
    If an additional approval is required Research IT approval workflow is followed.

- **Delete Rejected Objects From Staging - IGLead:**

  - When **_REJECTED_** by Information Governance, the Step Function task uses an AWS Lambda function (`handle_egress_rejection`)
    to delete staged objects from the Egress staging bucket (with the expectation that the researcher will review
    and submit a new egress request)

- **Notify Research IT:**

  - If the request is **_APPROVED_**, control is passed to a Step Function
    task which uses direct integration with Amazon SNS to:
    - Publish a notification to the Information Governance SNS topic
    - Format the notification to include:
      - File types
      - Egress Request ID
      - Research Project
      - Researcher Email
      - Information Governance Email

- **Research IT Decision:**

  - Step Function task which uses an AWS Lambda function (`update-egress-request-with-task-token-function`)
    to write a step function task token as an attribute of the egress request item in the DynamoDB table
  - The task pauses and waits for a callback which includes the token before it can resume execution
  - Callback will be received via a GraphQL API call from the frontend which will be processed by the `egress-api-handler`
  - Validation in the API will ensure that only the Research IT role can update the request at this point in time

- **Save Research IT Decision:**

  - Step Function task which uses direct integration with Amazon DynamoDB to update the Research IT decision
    in the DynamoDB table.
  - This task is triggered by the UpdateRequest API being invoked. The API invokes a Lambda function which uses
    the task token previously retrieved (when requests were loaded in the frontend) to resume the step
    function execution

- **Research IT Approved?:**

  - Step Function choice task which parses the status of the request as received from the frontend API call
    in the previous task to determine if the request was **_APPROVED_** or **_REJECTED_** by Research IT

- **Delete Rejected Objects From Staging - RIT:**

  - When **_REJECTED_** by Research IT, the Step Function task uses an AWS Lambda function (`handle_egress_rejection`)
    to delete staged objects from the Egress staging bucket (with the expectation that the researcher will review and
    submit a new egress request)

- **Copy Approved Objects to Datalake:**

  - If the request is **_APPROVED_**, control is passed to a Step Function task which uses an AWS Lambda function
    (`copy_egress_candidates_to_datalake`) to:
    - Download the approved egress objects unto an EFS file store that is attached to the Lambda function
    - Create a zip file containing all the objects
    - Upload the zip file to the datalake target S3 bucket
    - Clean up all related data from both the egress staging bucket and the EFS

- **Update Request in Egress Store DynamoDB (status):**

  - Step Function task which uses direct integration with Amazon DynamoDB to update the egress store item status in
    the SWB DynamoDB table as follows:

    | Egress App Status | SWB Egress Store Status |
    | :---------------: | :---------------------: |
    |     APPROVED      |        PROCESSED        |
    |     REJECTED      |         PENDING         |

  - Setting the status to **_PROCESSED_** allows the researcher to terminate the research workspace and
    associated egress store
  - Setting the status to **_PENDING_** allows the researcher to revise and resubmit the candidate egress data.
    They may also choose to terminate the research workspace and associated egress store at this stage.
    (They could not do so while the request was in a status of **_PROCESSING_** which is set when the egress
    request is first received by the step function.)

- **Notify Requester:**
  - Step Function task to send an email to the requester (e.g. researcher) with the Information Governance
    lead in copy. The email marks an egress request review as complete and provides instructions with next steps.
