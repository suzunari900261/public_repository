from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Fn,
    Tags,
    Duration,
    Size,
)
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as aws_s3
from aws_cdk import aws_sns as sns

class LambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        environment: str,
        topic: sns.ITopic,
        code_bucket: str,
        code_key: str,
    ) -> None:
        super().__init__(scope, construct_id)

        bucket = aws_s3.Bucket.from_bucket_name(self, "CodeBucket", code_bucket)

        # ------------------------------------------------------------
        # lambda.Function
        # ------------------------------------------------------------
        fn = _lambda.Function(
            self,
            "Lambda",
            function_name=f"{project_name}-{environment}-Lambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_bucket(bucket=bucket, key=code_key),
            environment={
                "TOPIC_ARN": topic.topic_arn,
            },
            timeout=Duration.seconds(3),
            memory_size=128,
            ephemeral_storage_size=Size.mebibytes(512),
        )

        # ------------------------------------------------------------
        # IAMRole
        # ------------------------------------------------------------
        topic.grant_publish(fn)

        Tags.of(fn).add("Name", f"{project_name}-{environment}")
        Tags.of(fn).add("Environment", environment)

        CfnOutput(
            self,"LambdaArn",
            value=fn.function_arn,
            export_name=f"{project_name}-{environment}-Lambda",
        )

        self.function = fn

        # ------------------------------------------------------------
        # Permission
        # ------------------------------------------------------------
    def allow_invoke_from_http_api(self, api_id: str) -> None:
        _lambda.CfnPermission(
            self,
            "AllowInvokeFromHttpApi",
            action="lambda:InvokeFunction",
            function_name=self.function.function_arn,
            principal="apigateway.amazonaws.com",
            source_arn=Fn.sub(
                "arn:${AWS::Partition}:execute-api:${AWS::Region}:${AWS::AccountId}:${ApiId}/*/*/*",
                {"ApiId": api_id},
            ),
        )