from constructs import Construct
from aws_cdk import Fn
from aws_cdk import aws_apigatewayv2 as apigwv2

class ApiGatewayConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        environment: str,
        cors_allow_origins: str,
        lambda_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        # ------------------------------------------------------------
        # API
        # ------------------------------------------------------------
        api = apigwv2.CfnApi(
            self,
            "APIGateway",
            name=Fn.sub("${ProjectName}-${Environment}-apigateway",
                {"ProjectName": project_name, "Environment": environment},
            ),
            protocol_type="HTTP",
            cors_configuration=apigwv2.CfnApi.CorsProperty(
                allow_credentials=True,
                allow_headers=["Content-Type", "Authorization"],
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_origins=[cors_allow_origins],
                max_age=3600,
            ),
            tags={
                "Name": Fn.sub("${ProjectName}-${Environment}",{
                    "ProjectName": project_name,
                    "Environment": environment,
                }),
                "Environment": environment,
            },
        )

        # ------------------------------------------------------------
        # integration
        # ------------------------------------------------------------
        integration = apigwv2.CfnIntegration(
            self,
            "Integration",
            api_id=api.ref,
            integration_type="AWS_PROXY",
            integration_method="POST",
            payload_format_version="2.0",
            timeout_in_millis=30000,
            integration_uri=lambda_arn,
        )

        # ------------------------------------------------------------
        # stage
        # ------------------------------------------------------------
        stage = apigwv2.CfnStage(
            self,
           "Stage",
            api_id=api.ref,
            stage_name=environment,
            auto_deploy=True,
        )

        # ------------------------------------------------------------
        # route
        # ------------------------------------------------------------
        route = apigwv2.CfnRoute(
            self,
            "Route",
            api_id=api.ref,
            route_key="POST /api/sns",
            authorization_type="NONE",
            target=Fn.join("/", ["integrations", integration.ref]),
        )
        route.add_dependency(integration)

        self.api_id = api.ref
        self.api_endpoint = api.attr_api_endpoint
