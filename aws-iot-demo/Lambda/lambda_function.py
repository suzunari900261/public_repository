import json
import os
import boto3
from datetime import datetime

cloudwatch = boto3.client("cloudwatch")

# 環境変数取得
NAMESPACE = os.environ.get("METRIC_NAMESPACE", "IoTDemo")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "prod")

def lambda_handler(event, context):
    """
    event example:
    {
      "deviceId": "iot-demo-dev-device-01",
      "location": "office-tokyo",
      "status": "alert",
      "alertReasons": ["high_temperature", "high_co2"]
    }
    """

    print("Received event:", json.dumps(event))

    if event.get("status") != "alert":
        print("Status is not alert. Skip.")
        return {"result": "skipped"}

    device_id = event.get("deviceId", "unknown")
    location = event.get("location", "unknown")
    alert_reasons = event.get("alertReasons", [])

    metric_data = []

    # 全異常共通カウント
    metric_data.append({
        "MetricName": "AlertCount",
        "Dimensions": [
            {"Name": "Environment", "Value": ENVIRONMENT},
            {"Name": "DeviceId", "Value": device_id},
            {"Name": "Location", "Value": location}
        ],
        "Timestamp": datetime.utcnow(),
        "Value": 1,
        "Unit": "Count"
    })

    # 異常種別ごとのメトリクス
    for reason in alert_reasons:
        metric_data.append({
            "MetricName": reason,
            "Dimensions": [
                {"Name": "Environment", "Value": ENVIRONMENT},
                {"Name": "DeviceId", "Value": device_id},
                {"Name": "Location", "Value": location}
            ],
            "Timestamp": datetime.utcnow(),
            "Value": 1,
            "Unit": "Count"
        })

    # CloudWatch に送信
    cloudwatch.put_metric_data(
        Namespace=NAMESPACE,
        MetricData=metric_data
    )

    print(f"Sent {len(metric_data)} metrics to CloudWatch")

    return {
        "result": "success",
        "metrics_sent": len(metric_data)
    }
