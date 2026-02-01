import aws_cdk as cdk
import aws_cdk.assertions as assertions

from cdk_python.frontend_stack import FrontendStack
from cdk_python.backend_stack import BackendStack


def test_frontend_stack_has_expected_resources_and_security():
    app = cdk.App()
    stack = FrontendStack(app, "TestFrontendStack")
    template = assertions.Template.from_stack(stack)

    # --- Resource presence (high-level architecture) ---
    template.resource_count_is("AWS::S3::Bucket", 1)
    template.resource_count_is("AWS::S3::BucketPolicy", 1)

    # CloudFront (L1 distribution + OAC)
    template.resource_count_is("AWS::CloudFront::Distribution", 1)
    template.resource_count_is("AWS::CloudFront::OriginAccessControl", 1)

    # --- S3 security posture ---
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
    )

    # --- Bucket policy restricts read to CloudFront via SourceArn condition ---
    # S3frontConstruct.grant_read_from_cloudfront() で設定している意図の検証
    template.has_resource_properties(
        "AWS::S3::BucketPolicy",
        {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with(
                    [
                        assertions.Match.object_like(
                            {
                                "Action": "s3:GetObject",
                                "Effect": "Allow",
                                "Principal": {"Service": "cloudfront.amazonaws.com"},
                                "Condition": {
                                    "StringEquals": {
                                        "AWS:SourceArn": assertions.Match.any_value()
                                    }
                                },
                            }
                        )
                    ]
                )
            }
        },
    )

    # --- CloudFront behavior / origins
    template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": assertions.Match.object_like(
                {
                    "Enabled": True,
                    "DefaultRootObject": "index.html",
                    "Origins": assertions.Match.array_with(
                        [
                            assertions.Match.object_like({"Id": "S3Origin"}),
                            assertions.Match.object_like({"Id": "APIGatewayOrigin"}),
                        ]
                    ),
                    "CacheBehaviors": assertions.Match.array_with(
                        [
                            assertions.Match.object_like({"PathPattern": "/api/*"})
                        ]
                    ),
                }
            )
        },
    )


def test_backend_stack_has_api_lambda_sns_and_permissions():
    app = cdk.App()
    stack = BackendStack(app, "TestBackendStack")
    template = assertions.Template.from_stack(stack)

    # --- SNS ---
    template.resource_count_is("AWS::SNS::Topic", 1)
    template.resource_count_is("AWS::SNS::Subscription", 1)

    # --- Lambda ---
    template.resource_count_is("AWS::Lambda::Function", 1)

    # Runtime/Handler/Env
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "lambda_function.lambda_handler",
            "Runtime": "python3.12",
            "Environment": {
                "Variables": {
                    "TOPIC_ARN": assertions.Match.any_value(),
                }
            },
        },
    )

    # --- API Gateway (HTTP API v2 / integration / route / stage) ---
    template.resource_count_is("AWS::ApiGatewayV2::Api", 1)
    template.resource_count_is("AWS::ApiGatewayV2::Integration", 1)
    template.resource_count_is("AWS::ApiGatewayV2::Route", 1)
    template.resource_count_is("AWS::ApiGatewayV2::Stage", 1)

    # RouteKey が期待通り（POST /api/sns)
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {
            "RouteKey": "POST /api/sns",
            "AuthorizationType": "NONE",
        },
    )

    # --- Lambda permission: API Gateway からの invoke 許可があること ---
    template.resource_count_is("AWS::Lambda::Permission", 1)
    template.has_resource_properties(
        "AWS::Lambda::Permission",
        {
            "Action": "lambda:InvokeFunction",
            "Principal": "apigateway.amazonaws.com",
        },
    )
