# (c) 2022 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at https://aws.amazon.com/agreement or other written
# agreement between Customer and Amazon Web Services, Inc.

import os
from datetime import datetime

import boto3
from aws_lambda_powertools import Logger, Tracer

MAX_REQUEST_AGE_DAYS = 90

tracer = Tracer(service="ListRequestsAPI")
logger = Logger(service="ListRequestsAPI")

ddb = boto3.resource("dynamodb")
table = os.environ["TABLE"]


def list_requests():
    logger.debug("List Requests API invoked")

    now = datetime.now()

    def is_recent(item):
        updated_dt = datetime.strptime(item["updated_dt"], "%Y-%m-%dT%H:%M:%S.%fZ")
        return (now - updated_dt).days < MAX_REQUEST_AGE_DAYS

    ddb_table = ddb.Table(table)

    response = ddb_table.scan()
    data = [item for item in response["Items"] if is_recent(item)]
    while response.get("LastEvaluatedKey"):
        response = ddb_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        data.extend([item for item in response["Items"] if is_recent(item)])

    logger.debug("Successful database scan of all egress requests")
    return data
