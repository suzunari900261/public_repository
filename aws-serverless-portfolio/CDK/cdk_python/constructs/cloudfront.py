from aws_cdk import aws_cloudfront as cloudfront, Fn
from constructs import Construct

class CloudfrontConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        bucket,
        domain_name: str,
        acm_certificate_arn: str,
        log_bucket_name: str,
        log_prefix: str = "cloudfront/",
        api_domain_name: str,
        api_origin_path: str,
    ) -> None:
        super().__init__(scope, id)

        log_bucket_domain = Fn.join("", [log_bucket_name, ".s3.amazonaws.com"])

        # ------------------------------------------------------------
        # Origin Access Control (OAC)
        # ------------------------------------------------------------
        self.oac = cloudfront.CfnOriginAccessControl(
            self,
            "OAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name=f"{id}-oac",
                signing_protocol="sigv4",
                signing_behavior="always",
                origin_access_control_origin_type="s3",
            ),
        )

        # ------------------------------------------------------------
        # APICachePolicy
        # ------------------------------------------------------------
        api_cache_policy = cloudfront.CfnCachePolicy(
            self, "ApiCachePolicy",
            cache_policy_config=cloudfront.CfnCachePolicy.CachePolicyConfigProperty(
                name=f"{id}-api-cache-policy",
                default_ttl=0,
                min_ttl=0,
                max_ttl=0,
                parameters_in_cache_key_and_forwarded_to_origin=cloudfront.CfnCachePolicy.ParametersInCacheKeyAndForwardedToOriginProperty(
                    enable_accept_encoding_gzip=False,
                    enable_accept_encoding_brotli=False,
                    cookies_config=cloudfront.CfnCachePolicy.CookiesConfigProperty(cookie_behavior="none"),
                    headers_config=cloudfront.CfnCachePolicy.HeadersConfigProperty(header_behavior="none"),
                    query_strings_config=cloudfront.CfnCachePolicy.QueryStringsConfigProperty(query_string_behavior="none"),
                ),
            ),
        )

        # ------------------------------------------------------------
        # APIOriginRequestPolicy
        # ------------------------------------------------------------
        api_origin_request_policy = cloudfront.CfnOriginRequestPolicy(
            self, "ApiOriginRequestPolicy",
            origin_request_policy_config=cloudfront.CfnOriginRequestPolicy.OriginRequestPolicyConfigProperty(
                name=f"{id}-api-origin-request-policy",
                headers_config=cloudfront.CfnOriginRequestPolicy.HeadersConfigProperty(
                    header_behavior="whitelist",
                    headers=["Content-Type", "Origin", "Referer"],
                ),
                cookies_config=cloudfront.CfnOriginRequestPolicy.CookiesConfigProperty(cookie_behavior="none"),
                query_strings_config=cloudfront.CfnOriginRequestPolicy.QueryStringsConfigProperty(query_string_behavior="all"),
            ),
        )

        # ------------------------------------------------------------
        # CloudFront Distribution
        # ------------------------------------------------------------
        self.distribution = cloudfront.CfnDistribution(
            self,
            "Distribution",
            distribution_config=cloudfront.CfnDistribution.DistributionConfigProperty(
                enabled=True,
                default_root_object="index.html",
                price_class="PriceClass_100",

                logging=cloudfront.CfnDistribution.LoggingProperty(
                    bucket=log_bucket_domain,
                    prefix=log_prefix,
                    include_cookies=False,
                ),

                aliases=[
                    domain_name,
                    f"www.{domain_name}",
                ],

                viewer_certificate=cloudfront.CfnDistribution.ViewerCertificateProperty(
                    acm_certificate_arn=acm_certificate_arn,
                    ssl_support_method="sni-only",
                    minimum_protocol_version="TLSv1.2_2021",
                ),

                origins=[
                    cloudfront.CfnDistribution.OriginProperty(
                        id="S3Origin",
                        domain_name=bucket.bucket_regional_domain_name,
                        s3_origin_config=cloudfront.CfnDistribution.S3OriginConfigProperty(
                            origin_access_identity="" 
                        ),
                        origin_access_control_id=self.oac.ref,
                    ),
                    cloudfront.CfnDistribution.OriginProperty(
                        id="APIGatewayOrigin",
                        domain_name=api_domain_name,
                        origin_path=api_origin_path,
                        custom_origin_config=cloudfront.CfnDistribution.CustomOriginConfigProperty(
                            origin_protocol_policy="https-only",
                            origin_ssl_protocols=["TLSv1.2"],
                        ),
                    ),
                ],
                default_cache_behavior=cloudfront.CfnDistribution.DefaultCacheBehaviorProperty(
                    target_origin_id="S3Origin",
                    viewer_protocol_policy="redirect-to-https",
                    allowed_methods=["GET", "HEAD"],
                    cached_methods=["GET", "HEAD"],
                    forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                        query_string=False,
                    ),
                ),
                cache_behaviors=[
                    cloudfront.CfnDistribution.CacheBehaviorProperty(
                        path_pattern="/api/*",
                        target_origin_id="APIGatewayOrigin",
                        viewer_protocol_policy="redirect-to-https",
                        allowed_methods=["GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"],
                        cached_methods=["GET","HEAD"],
                        cache_policy_id=api_cache_policy.ref,
                        origin_request_policy_id=api_origin_request_policy.ref,
                    )
                ],
                custom_error_responses=[
                    cloudfront.CfnDistribution.CustomErrorResponseProperty(
                        error_code=403,
                        response_code=200,
                        response_page_path="/index.html",
                        error_caching_min_ttl=0,
                    ),
                    cloudfront.CfnDistribution.CustomErrorResponseProperty(
                        error_code=404,
                        response_code=200,
                        response_page_path="/index.html",
                        error_caching_min_ttl=0,
                    ),
                ],
            ),
        )
