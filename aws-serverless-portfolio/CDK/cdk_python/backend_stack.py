from aws_cdk import (
    CfnOutput,
    CfnParameter,
    Stack,
    Tags,
)
from constructs import Construct

# Custom Constructs
from cdk_python.constructs.sns_topic import SnsTopicConstruct
from cdk_python.constructs.lambda_function import LambdaConstruct
from cdk_python.constructs.apigateway import ApiGatewayConstruct

class BackendStack(Stack):
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

        sns_endpoint_email = CfnParameter(
            self,
            "SNSEndpointEmail",
            type="String",
            description="Email for contact notification subscription",
        )

        lambda_code_bucket = CfnParameter(
            self,
            "LambdaCodeBucket",
            type="String",
        )

        lambda_code_key = CfnParameter(
            self,
            "LambdaCodeKey",
            type="String",
        )

        cors_allow_origins = CfnParameter(
            self,
            "CORSAllowOrigins",
            type="String",
        )

        # ------------------------------------------------------------
        # Tags
        # ------------------------------------------------------------

        Tags.of(self).add("Project", project_name.value_as_string)
        Tags.of(self).add("Env", environment.value_as_string)

        # ------------------------------------------------------------
        # Resources
        # ------------------------------------------------------------

        sns_construct = SnsTopicConstruct(
            self,
            "Sns",
            project_name=project_name.value_as_string,
            environment=environment.value_as_string,
            sns_endpoint_email=sns_endpoint_email.value_as_string,
        )

        lambda_construct = LambdaConstruct(
            self,
            "Lambda",
            project_name=project_name.value_as_string,
            environment=environment.value_as_string,
            topic=sns_construct.topic,
            code_bucket=lambda_code_bucket.value_as_string,
            code_key=lambda_code_key.value_as_string,
        )

        apigateway_construct = ApiGatewayConstruct(
            self,
            "Apigateway",
            project_name=project_name.value_as_string,
            environment=environment.value_as_string,
            cors_allow_origins=cors_allow_origins.value_as_string,
            lambda_arn=lambda_construct.function.function_arn,
        )

        lambda_construct.allow_invoke_from_http_api(apigateway_construct.api_id)

        # ------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------

        api_domain = f"{apigateway_construct.api_id}.execute-api.{self.region}.amazonaws.com"

        CfnOutput(
            self,
            "HttpApiDomainOutput",
            value=api_domain,
            export_name=f"{project_name.value_as_string}-{environment.value_as_string}-HttpApiDomain",
        )
