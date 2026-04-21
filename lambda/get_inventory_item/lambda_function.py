import json
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

#
TABLE_NAME = os.environ.get("TABLE_NAME", "Inventory")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }


def lambda_handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        item_id = path_params.get("id")

        if not item_id:
            return build_response(400, {
                "message": "Missing item id in path."
            })

        response = table.query(
            KeyConditionExpression=Key("Item_id").eq(item_id)
        )

        items = response.get("Items", [])

        if not items:
            return build_response(404, {
                "message": f"Item with id '{item_id}' not found."
            })

        return build_response(200, {
            "message": "Inventory item retrieved successfully.",
            "item": items[0]
        })

    except Exception as error:
        return build_response(500, {
            "message": "Failed to retrieve inventory item.",
            "error": str(error)
        })