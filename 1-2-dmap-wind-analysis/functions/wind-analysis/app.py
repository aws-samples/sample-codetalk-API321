import json
import os
import csv
import io

from datetime import datetime
from decimal import Decimal
from typing import Dict, List

import boto3


S3_CLIENT = boto3.client("s3")


def lambda_handler(event: dict, context):
    """Handler that will find the weather station that has the highest average wind speed by month.

    Returns a dictionary with "year-month" as the key and dictionary (weather station info) as value.

    """
    input_bucket_name = os.environ["INPUT_BUCKET_NAME"]

    high_by_month: Dict[str, Dict] = {}

    for item in event["Items"]:
        csv_data = get_file_from_s3(input_bucket_name, item["Key"])
        dict_data = get_csv_dict_from_string(csv_data)

        for row in dict_data:
            # avg_temp = float(row["TEMP"])
            avg_wind_speed = Decimal(row["WDSP"])
            if avg_wind_speed == 999.9:
                avg_wind_speed = 0.0

            date = datetime.fromisoformat(row["DATE"])
            month_str = date.strftime("%Y-%m")

            monthly_high_record = high_by_month.get(month_str) or {}

            if not monthly_high_record:
                # row["TEMP"] = avg_temp
                
                row["WDSP"] = avg_wind_speed
                high_by_month[month_str] = row
                continue

            if avg_wind_speed > float(monthly_high_record["WDSP"]):
                high_by_month[month_str] = row
                
    return high_by_month


def reducer_handler(event: dict, context: dict):
    """Reducer function will read all of the mapped results from S3 and write to DDB.

    Args:
        event (dict): The event payload that arrives after the distributed map run has the
        folllowing structure:

            {
            "MapRunArn": "arn-of-the-map-run",
            "ResultWriterDetails": {
                "Bucket": "bucket-name-where-results-are-written",
                "Key": "results/dee8fb57-3653-3f09-88dd-4f39225d2367/manifest.json",
            },
        }
        context (dict): Lambda context
    """
    results_bucket = event["ResultWriterDetails"]["Bucket"]
    manifest = get_file_from_s3(
        results_bucket,
        event["ResultWriterDetails"]["Key"],
    )

    maniftest_json = json.loads(manifest)

    high_by_month: Dict[str, Dict] = {}

    for result in maniftest_json["ResultFiles"].get("SUCCEEDED", []):
        results = get_file_from_s3(results_bucket, result["Key"])

        for json_result in json.loads(results):

            monthly_highs: Dict[str, Dict] = json.loads(json_result["Output"])

            for month_str, row in monthly_highs.items():
                high_wind_speed = Decimal(row["WDSP"])
                # if high_wind_speed == Decimal('999.9'):
                #     high_wind_speed = Decimal('0.0')
                #     row["WDSP"] = '0.0'

                monthly_high = high_by_month.get(month_str)

                if not monthly_high:
                    high_by_month[month_str] = row
                    continue

                if high_wind_speed > Decimal(monthly_high["WDSP"]):
                    high_by_month[month_str] = row

    _write_results_to_ddb(high_by_month)
    _write_results_to_s3(high_by_month, event["ResultWriterDetails"]["Key"])

def _write_results_to_s3(high_by_month: Dict[str, Dict], key: str):
    output_bucket = os.environ["RESULTS_BUCKET_NAME"]
    
    parts = key.split('/')
    key = '/'.join(parts[:2] + parts[3:])
    
    key=f"{key}/wind_speed_results.csv"
    
    print(key)
    
    # Convert to CSV format
    if not high_by_month:
        return
    
    fieldnames = list(next(iter(high_by_month.values())).keys())
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    
    for month_str, row in high_by_month.items():
        row["pk"] = month_str
        writer.writerow(row)
    
    S3_CLIENT.put_object(
        Bucket=output_bucket,
        Key=key,
        Body=csv_buffer.getvalue().encode("utf-8"),
        ContentType="text/csv"
    )

def _write_results_to_ddb(high_by_month: Dict[str, Dict]):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["RESULTS_DYNAMODB_TABLE_NAME"])

    for month_str, row in high_by_month.items():
        row["pk"] = month_str
        row["WDSP"] = round(Decimal(row["WDSP"]), 1)
        table.put_item(Item=row)


def get_file_from_s3(input_bucket_name: str, key: str) -> str:
    resp = S3_CLIENT.get_object(Bucket=input_bucket_name, Key=key)
    return resp["Body"].read().decode("utf-8")


def get_csv_dict_from_string(csv_string: str) -> dict:
    return csv.DictReader(io.StringIO(csv_string))
