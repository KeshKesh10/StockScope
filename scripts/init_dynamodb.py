from __future__ import annotations

import os

import boto3
from botocore.exceptions import ClientError


def ensure_table(client, table_name: str, schema: dict) -> None:
    try:
        client.describe_table(TableName=table_name)
        print(f"Table already exists: {table_name}")
        return
    except client.exceptions.ResourceNotFoundException:
        pass

    client.create_table(TableName=table_name, **schema)
    waiter = client.get_waiter("table_exists")
    waiter.wait(TableName=table_name)
    print(f"Created table: {table_name}")


def main() -> None:
    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL", "http://localhost:8000")
    region = os.environ.get("AWS_REGION", "us-east-1")
    users_table = os.environ.get("USERS_TABLE", "stockscope-users")
    favorites_table = os.environ.get("FAVORITES_TABLE", "stockscope-favorites")
    signups_table = os.environ.get("SIGNUPS_TABLE", "stockscope-signups")

    client = boto3.client(
        "dynamodb",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "local"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "local"),
    )

    ensure_table(
        client,
        users_table,
        {
            "AttributeDefinitions": [
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "username", "AttributeType": "S"},
            ],
            "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
            "BillingMode": "PAY_PER_REQUEST",
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "username-index",
                    "KeySchema": [{"AttributeName": "username", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        },
    )

    ensure_table(
        client,
        favorites_table,
        {
            "AttributeDefinitions": [
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "ticker", "AttributeType": "S"},
                {"AttributeName": "industry_sort", "AttributeType": "S"},
            ],
            "KeySchema": [
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "ticker", "KeyType": "RANGE"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "user-industry-index",
                    "KeySchema": [
                        {"AttributeName": "user_id", "KeyType": "HASH"},
                        {"AttributeName": "industry_sort", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        },
    )

    ensure_table(
        client,
        signups_table,
        {
            "AttributeDefinitions": [
                {"AttributeName": "signup_id", "AttributeType": "S"},
                {"AttributeName": "category", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
            ],
            "KeySchema": [{"AttributeName": "signup_id", "KeyType": "HASH"}],
            "BillingMode": "PAY_PER_REQUEST",
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "category-index",
                    "KeySchema": [
                        {"AttributeName": "category", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        },
    )


if __name__ == "__main__":
    main()
