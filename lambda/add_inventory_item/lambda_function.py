import json
import os
import uuid
from decimal import Decimal, InvalidOperation

import boto3


TABLE_NAME = os.environ.get("TABLE_NAME", "Inventory")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


try:
    import ulid
except ImportError:
    ulid = None


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


def generate_item_id():
    if ulid:
        return str(ulid.new())
    return str(uuid.uuid4())


def lambda_handler(event, context):
    try:
        raw_body = event.get("body")
        if not raw_body:
            return build_response(400, {
                "message": "Request body is required."
            })

        body = json.loads(raw_body)

        required_fields = [
            "item_name",
            "item_description",
            "Item_qty",
            "Item_price",
            "location_id"
        ]

        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            return build_response(400, {
                "message": "Missing required fields.",
                "missing_fields": missing_fields
            })

        item_name = str(body["item_name"]).strip()
        item_description = str(body["item_description"]).strip()

        if not item_name:
            return build_response(400, {
                "message": "item_name cannot be empty."
            })

        if not item_description:
            return build_response(400, {
                "message": "item_description cannot be empty."
            })

        try:
            item_qty = int(body["Item_qty"])
        except (ValueError, TypeError):
            return build_response(400, {
                "message": "Item_qty must be an integer."
            })

        if item_qty < 0:
            return build_response(400, {
                "message": "Item_qty cannot be negative."
            })

        try:
            item_price = Decimal(str(body["Item_price"]))
        except (InvalidOperation, ValueError, TypeError):
            return build_response(400, {
                "message": "Item_price must be a valid number."
            })

        if item_price < 0:
            return build_response(400, {
                "message": "Item_price cannot be negative."
            })

        try:
            location_id = int(body["location_id"])
        except (ValueError, TypeError):
            return build_response(400, {
                "message": "location_id must be an integer."
            })

        item = {
            "Item_id": generate_item_id(),
            "location_id": location_id,
            "item_name": item_name,
            "item_description": item_description,
            "Item_qty": item_qty,
            "Item_price": item_price
        }

        table.put_item(Item=item)

        return build_response(201, {
            "message": "Inventory item added successfully.",
            "item": item
        })

    except json.JSONDecodeError:
        return build_response(400, {
            "message": "Request body must be valid JSON."
        })
    except Exception as error:
        return build_response(500, {
            "message": "Failed to add inventory item.",
            "error": str(error)
        })