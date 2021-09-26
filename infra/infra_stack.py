from aws_cdk import core as cdk
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as route53_targets
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_certificatemanager as acm

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class InfraStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        arn = self.node.try_get_context("cert_arn")
        bucket = s3.Bucket(
            self,
            id="myBucket",
            bucket_name=self.node.try_get_context("bucket_site_name")
        )

        '''
        bucket = s3.Bucket.from_bucket_name(
            self,
            id="myBucket",
            bucket_name=self.node.try_get_context("bucket_site_name")
        )
        '''

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            id="myHostedZone",
            hosted_zone_id=self.node.try_get_context("route53_zone_id"),
            zone_name=self.node.try_get_context("ssl_domain_name")
        )

        ssl_certificate = acm.Certificate.from_certificate_arn(
            self,
            id="MyCertificate",
            certificate_arn=arn
        )

        viewer_certificate = cloudfront.ViewerCertificate.from_acm_certificate(certificate=ssl_certificate)

        origin_access_identity = cloudfront.OriginAccessIdentity(self, id="OriginAccessIdentity")
        bucket.grant_read(origin_access_identity)

        distribution = cloudfront.CloudFrontWebDistribution(
            self,
            id="myCloudfrontWebDistribution",
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=bucket,
                        origin_access_identity=origin_access_identity),
                    behaviors=[
                        cloudfront.Behavior(
                            is_default_behavior=True,
                            default_ttl=core.Duration.hours(1)
                        )
                    ]
                )
            ],
            viewer_certificate=viewer_certificate,
            default_root_object="index.html",
        )

        route53.ARecord(
            self,
            id="AliasRecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(distribution))
        )
