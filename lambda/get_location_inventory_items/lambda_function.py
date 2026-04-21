import json
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key


TABLE_NAME = os.environ.get("TABLE_NAME", "Inventory")
LOCATION_INDEX_NAME = os.environ.get("LOCATION_INDEX_NAME", "location_id-Item_id-index")

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
        location_id_value = path_params.get("id")

        if location_id_value is None:
            return build_response(400, {
                "message": "Missing location id in path."
            })

        try:
            location_id = int(location_id_value)
        except (ValueError, TypeError):
            return build_response(400, {
                "message": "location id must be an integer."
            })

        response = table.query(
            IndexName=LOCATION_INDEX_NAME,
            KeyConditionExpression=Key("location_id").eq(location_id)
        )

        return build_response(200, {
            "message": "Location inventory items retrieved successfully.",
            "location_id": location_id,
            "items": response.get("Items", [])
        })

    except Exception as error:
        return build_response(500, {
            "message": "Failed to retrieve location inventory items.",
            "error": str(error)
        })