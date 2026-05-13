"""
Batch delete forms from DynamoDB (homolog) and their associated S3 files.

Usage:
    python scripts/batch_delete_forms.py [--dry-run]

    --dry-run   Show what would be deleted without actually deleting anything.
"""

import sys
import boto3
from boto3.dynamodb.conditions import Key

REGION = "sa-east-1"
TABLE_NAME = "FormulariosStackhomolog-FormulariosDynamoFormulariosTableAD86E94B-1V21Y9MXZGEBT"
BUCKET_NAME = "formularios-homolog"
PK = "PK"
SK = "SK"

FORM_IDS = [
    "0cee3316-df41-4c1c-8206-d17e1cd789d6",
    "28eaa121-43f9-4f79-8fbd-2d5c12768a6d",
    "82c58d6a-741d-4d27-a326-8a1371fbda82",
    "bc37cafd-430d-473f-9375-6fa67fce0cd4",
    "9994b78a-07b2-4eb1-bb35-3f7375c54f6d",
    "b44054cb-8d2f-48b7-b61b-03e5da6d584a",
    "80143e00-37d5-42da-a026-7ca8c22ac3a5",
    "a164260c-c79c-487e-8f4e-c1e0c6b5335e",
    "d5a19d9f-30c8-45a1-8463-a8e5e3fffbfa",
    "4a0c955f-7f02-490e-b57f-3652286cd3ae",
    "720fc003-7994-47f7-9407-3687e0abf4ff",
    "91e90ebf-a0b4-4781-a6b4-4fb62edff313",
    "7f984f80-15e2-4a53-a861-555ee61a3381",
    "e2fbeddd-e8c7-44ce-8f5d-ca11a30b87bf",
    "7639d44b-e631-4dda-a578-8bc249480c6f",
]


def get_dynamo_table():
    session = boto3.Session(region_name=REGION)
    dynamodb = session.resource("dynamodb")
    return dynamodb.Table(TABLE_NAME)


def get_s3_client():
    session = boto3.Session(region_name=REGION)
    return session.client("s3")


def find_all_items_for_form(table, form_id: str) -> list[dict]:
    """Query all items with PK = form#{form_id} (could have multiple SK values)."""
    resp = table.query(
        KeyConditionExpression=Key(PK).eq(f"form#{form_id}"),
        Select="ALL_ATTRIBUTES",
    )
    items = resp.get("Items", [])

    while "LastEvaluatedKey" in resp:
        resp = table.query(
            KeyConditionExpression=Key(PK).eq(f"form#{form_id}"),
            Select="ALL_ATTRIBUTES",
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    return items


def delete_dynamo_items(table, items: list[dict], dry_run: bool):
    """Batch-delete all given items from DynamoDB."""
    keys = [{PK: item[PK], SK: item[SK]} for item in items if PK in item and SK in item]

    if not keys:
        return 0

    if dry_run:
        for key in keys:
            print(f"  [DRY-RUN] Would delete DynamoDB item: {key}")
        return len(keys)

    with table.batch_writer() as batch:
        for key in keys:
            batch.delete_item(Key=key)

    return len(keys)


def find_s3_objects_for_form(s3_client, form_id: str) -> list[str]:
    """List all S3 objects that contain the form_id in their key."""
    # S3 paths follow: {year}/{system}/{form_id}/...
    # We can't know the year/system, so we search by listing with a paginator
    paginator = s3_client.get_paginator("list_objects_v2")
    matching_keys = []

    try:
        for page in paginator.paginate(Bucket=BUCKET_NAME):
            for obj in page.get("Contents", []):
                if form_id in obj["Key"]:
                    matching_keys.append(obj["Key"])
    except s3_client.exceptions.NoSuchBucket:
        print(f"  [WARN] Bucket '{BUCKET_NAME}' not found. Skipping S3 cleanup.")
        return []
    except Exception as e:
        print(f"  [WARN] Error listing S3 objects: {e}. Skipping S3 cleanup.")
        return []

    return matching_keys


def delete_s3_objects(s3_client, keys: list[str], dry_run: bool):
    """Delete S3 objects by key."""
    if not keys:
        return 0

    if dry_run:
        for key in keys:
            print(f"  [DRY-RUN] Would delete S3 object: s3://{BUCKET_NAME}/{key}")
        return len(keys)

    # S3 delete_objects supports up to 1000 keys per call
    for i in range(0, len(keys), 1000):
        batch = keys[i : i + 1000]
        s3_client.delete_objects(
            Bucket=BUCKET_NAME,
            Delete={"Objects": [{"Key": k} for k in batch], "Quiet": True},
        )

    return len(keys)


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN MODE — nothing will be deleted ===\n")

    table = get_dynamo_table()
    s3_client = get_s3_client()

    total_dynamo = 0
    total_s3 = 0

    print(f"Table:  {TABLE_NAME}")
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Forms:  {len(FORM_IDS)}\n")

    # --- Phase 1: Collect all DynamoDB items ---
    all_items = []
    for form_id in FORM_IDS:
        items = find_all_items_for_form(table, form_id)
        if items:
            print(f"[DynamoDB] form_id={form_id} -> {len(items)} item(s) found")
            all_items.extend(items)
        else:
            print(f"[DynamoDB] form_id={form_id} -> NOT FOUND")

    # --- Phase 2: Delete DynamoDB items ---
    if all_items:
        count = delete_dynamo_items(table, all_items, dry_run)
        total_dynamo = count
        action = "would delete" if dry_run else "deleted"
        print(f"\n[DynamoDB] {action} {count} item(s) total.\n")
    else:
        print("\n[DynamoDB] No items found to delete.\n")

    # --- Phase 3: Find and delete S3 objects ---
    print("Scanning S3 for associated files...")
    all_s3_keys = []
    for form_id in FORM_IDS:
        keys = find_s3_objects_for_form(s3_client, form_id)
        if keys:
            print(f"[S3] form_id={form_id} -> {len(keys)} file(s) found")
            all_s3_keys.extend(keys)

    if all_s3_keys:
        count = delete_s3_objects(s3_client, all_s3_keys, dry_run)
        total_s3 = count
        action = "would delete" if dry_run else "deleted"
        print(f"\n[S3] {action} {count} file(s) total.\n")
    else:
        print("\n[S3] No files found.\n")

    # --- Summary ---
    print("=" * 50)
    action = "Would delete" if dry_run else "Deleted"
    print(f"{action}: {total_dynamo} DynamoDB items, {total_s3} S3 files")
    if dry_run:
        print("\nRe-run without --dry-run to execute the deletions.")


if __name__ == "__main__":
    main()
