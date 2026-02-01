from aws_cdk import (
    aws_s3 as s3,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct


class S3frontConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        bucket_name: str,
    ) -> None:
        super().__init__(scope, id)

        # ------------------------------------------------------------
        # S3 Bucket
        # ------------------------------------------------------------

        self.bucket = s3.Bucket(
            self,
            "Bucket",
            bucket_name=bucket_name,
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

    # ------------------------------------------------------------
    # CloudFront OAC 用 Bucket Policy
    # ------------------------------------------------------------
    def grant_read_from_cloudfront(
        self,
        *,
        cloudfront_distribution_arn: str,
    ) -> None:
        """
        CloudFront OAC からの GetObject のみを許可する
        """

        self.bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowCloudFrontServicePrincipalReadOnly",
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.ServicePrincipal("cloudfront.amazonaws.com")
                ],
                actions=["s3:GetObject"],
                resources=[f"{self.bucket.bucket_arn}/*"],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": cloudfront_distribution_arn
                    }
                },
            )
        )
