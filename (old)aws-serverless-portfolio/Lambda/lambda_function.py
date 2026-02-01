import json
import boto3
import os

sns = boto3.client("sns")

TOPIC_ARN = os.environ["TOPIC_ARN"]

def lambda_handler(event, context):
    body = json.loads(event["body"])

    message = f"""
【ポートフォリオ 問い合わせ通知】

名前: {body['name']}
メール: {body['email']}
内容:
{body['message']}
"""

    sns.publish(
        TopicArn=TOPIC_ARN,
        Message=message,
        Subject="ポートフォリオサイト 問い合わせ"
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "ok"})
    }
