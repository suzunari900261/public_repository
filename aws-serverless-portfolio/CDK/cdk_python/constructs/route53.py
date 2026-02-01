from constructs import Construct
from aws_cdk import RemovalPolicy, CfnCondition, Fn
from aws_cdk import aws_route53 as route53


class Route53Construct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        domain_name: str,
        hosted_zone_id: str,
        cloudfront_domain_name: str,
    ) -> None:
        super().__init__(scope, construct_id)

        create_zone = CfnCondition(
            self,
            "CreateHostedZone",
            expression=Fn.condition_equals(hosted_zone_id, ""),
        )

        # ------------------------------------------------------------
        # HostedZone
        # ------------------------------------------------------------
        created_zone = route53.PublicHostedZone(
            self,
            "CreatedHostedZone",
            zone_name=domain_name,
            comment="Hosted zone for portfolio",
        )
        created_zone.apply_removal_policy(RemovalPolicy.RETAIN)
        created_zone.node.default_child.cfn_options.condition = create_zone

        record_hosted_zone_id = Fn.condition_if(
            create_zone.logical_id,
            created_zone.hosted_zone_id,
            hosted_zone_id,
        ).to_string()

        CLOUDFRONT_ZONE_ID = "Z2FDTNDATAQYW2"

        # ------------------------------------------------------------
        # Record
        # ------------------------------------------------------------
        route53.CfnRecordSet(
            self,
            "ARecordToCloudFront",
            hosted_zone_id=record_hosted_zone_id,
            name=domain_name,
            type="A",
            alias_target=route53.CfnRecordSet.AliasTargetProperty(
                dns_name=cloudfront_domain_name,
                hosted_zone_id=CLOUDFRONT_ZONE_ID,
                evaluate_target_health=False,
            ),
        )

        route53.CfnRecordSet(
            self,
            "ARecordWwwToCloudFront",
            hosted_zone_id=record_hosted_zone_id,
            name=f"www.{domain_name}",
            type="A",
            alias_target=route53.CfnRecordSet.AliasTargetProperty(
                dns_name=cloudfront_domain_name,
                hosted_zone_id=CLOUDFRONT_ZONE_ID,
                evaluate_target_health=False,
            ),
        )