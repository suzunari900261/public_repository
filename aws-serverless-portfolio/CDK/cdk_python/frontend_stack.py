from aws_cdk import (
    CfnOutput,
    CfnParameter,
    RemovalPolicy,
    Stack,
    Tags,
    aws_s3 as s3,
)
from constructs import Construct

# Custom Constructs
from cdk_python.constructs.s3_bucket import S3frontConstruct
from cdk_python.constructs.cloudfront import CloudfrontConstruct
from cdk_python.constructs.route53 import Route53Construct

class FrontendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------------
        # Parameters
        # ------------------------------------------------------------

        project_name = CfnParameter(
            self,
            "ProjectName",
            type="String",
            description="Project name for tagging and resource naming",
        )

        environment = CfnParameter(
            self,
            "Environment",
            type="String",
            default="prod",
            allowed_values=["dev", "prod"],
            description="Deployment environment",
        )

        s3_bucket_name = CfnParameter(
            self,
            "S3BucketName",
            type="String",
            description="S3 bucket name for static hosting",
        )

        domain_name = CfnParameter(
            self,
            "DomainName",
            type="String",
            description="Main domain name (e.g. example.com)",
        )

        hosted_zone_id = CfnParameter(
            self,
            "HostedZoneId",
            type="String",
            default="",
            description="(Optional) Existing Route53 Hosted Zone ID. If empty, create a new hosted zone.",
        )

        acm_certificate_arn = CfnParameter(
            self,
            "ACMCertificateArn",
            type="String",
        )

        log_bucket_name = CfnParameter(
            self,
            "CloudFrontLogBucketName",
            type="String",
        )

        api_domain_name = CfnParameter(
            self,
            "ApiDomainName",
            type="String",
            description="API Gateway domain (e.g. xxxx.execute-api.ap-northeast-1.amazonaws.com or custom domain)",
        )

        api_origin_path = CfnParameter(
            self,
            "ApiOriginPath",
            type="String",
            default="/prod",
            description="Origin path for API stage (e.g. /prod)",
        )

        # ------------------------------------------------------------
        # Tags
        # ------------------------------------------------------------

        Tags.of(self).add("Project", project_name.value_as_string)
        Tags.of(self).add("Env", environment.value_as_string)

        # ------------------------------------------------------------
        # Resources
        # ------------------------------------------------------------

        s3_construct = S3frontConstruct(
            self,
            "S3frontConstruct",
            bucket_name=s3_bucket_name.value_as_string,
        )

        cloudfront_construct = CloudfrontConstruct(
            self,
            "CloudfrontConstruct",
            bucket=s3_construct.bucket,
            domain_name=domain_name.value_as_string,
            acm_certificate_arn=acm_certificate_arn.value_as_string,
            log_bucket_name=log_bucket_name.value_as_string,
            log_prefix="cloudfront/",
            api_domain_name=api_domain_name.value_as_string,
            api_origin_path=api_origin_path.value_as_string,
        )

        cloudfront_distribution_arn = Stack.of(self).format_arn(
            service="cloudfront",
            resource="distribution",
            resource_name=cloudfront_construct.distribution.ref,
            region="",
            account=Stack.of(self).account,
        )

        s3_construct.grant_read_from_cloudfront(
            cloudfront_distribution_arn=cloudfront_distribution_arn
        )

        domain = Route53Construct(
            self,
            "Route53Construct",
            domain_name=domain_name.value_as_string,
            hosted_zone_id=hosted_zone_id.value_as_string,
            cloudfront_domain_name=cloudfront_construct.distribution.attr_domain_name,
        )
        # ------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------

        CfnOutput(
            self,
            "S3BucketNameOutput",
            value=s3_construct.bucket.bucket_name,
        )

        CfnOutput(
            self,
            "CloudFrontDomainNameOutput",
            value=cloudfront_construct.distribution.attr_domain_name,
        )
