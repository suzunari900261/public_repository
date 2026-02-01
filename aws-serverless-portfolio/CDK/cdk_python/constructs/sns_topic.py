from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Tags,
)
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subs


class SnsTopicConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        environment: str,
        sns_endpoint_email: str,
    ) -> None:
        super().__init__(scope, construct_id)

        topic_name = f"{project_name}-{environment}-contact-notification"

        # ------------------------------------------------------------
        # Topic
        # ------------------------------------------------------------
        self.topic = sns.Topic(
            self,
            "ContactNotificationTopic",
            topic_name=topic_name,
        )

        Tags.of(self.topic).add("Name", f"{project_name}-{environment}")
        Tags.of(self.topic).add("Environment", environment)

        # ------------------------------------------------------------
        # Subscription (email)
        # ------------------------------------------------------------
        self.topic.add_subscription(
            subs.EmailSubscription(sns_endpoint_email)
        )

        CfnOutput(
            self,
            "ContactNotificationTopicOutput",
            value=self.topic.topic_arn,
            export_name=f"{project_name}-{environment}-contact-notification",
        )
