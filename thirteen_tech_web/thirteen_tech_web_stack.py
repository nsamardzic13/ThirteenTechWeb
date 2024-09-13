import json
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct

# Load the configuration from a JSON file
with open("config.json", "r") as f:
    config = json.load(f)


class ThirteenTechWebStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a Route 53 hosted zone (or use an existing one)
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=config["customDomain"]
        )

        # Reference the manually created ACM certificate by ARN
        certificate = acm.DnsValidatedCertificate(
            self,
            "WebsiteCertificate",
            domain_name=config["customDomain"],
            subject_alternative_names=["*." + config["customDomain"]],
            hosted_zone=hosted_zone,
            region="us-east-1",  # cloudfront forced
        )
        certificate.apply_removal_policy(RemovalPolicy.DESTROY)
        CfnOutput(self, "Certificate", value=certificate.certificate_arn)

        # Create an S3 bucket for static website hosting
        bucket = s3.Bucket(
            self,
            "StaticWebsiteBucket",
            bucket_name=config["bucketName"],
            website_index_document="index.html",  # Index document
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,  # Allow public access but block ACLs
            removal_policy=RemovalPolicy.DESTROY,  # Destroy bucket on stack deletion
            auto_delete_objects=True,
        )
        CfnOutput(self, "BucketCfn", value=bucket.bucket_name)

        # Create a CloudFront distribution with the S3 bucket as the origin
        distribution = cloudfront.Distribution(
            self,
            "CloudFrontDistribution",
            certificate=certificate,
            default_root_object="index.html",
            domain_names=[config["customDomain"], "www." + config["customDomain"]],
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            default_behavior={
                "origin": origins.S3BucketOrigin(bucket),
                "compress": True,
                "allowed_methods": cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                "viewer_protocol_policy": cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            },
        )
        CfnOutput(self, "CloudFrontDistributionCfn", value=distribution.distribution_id)

        # Add an A record in Route 53 pointing to the CloudFront distribution
        route53.ARecord(
            self,
            "AliasRecord",
            zone=hosted_zone,
            record_name=config["customDomain"],
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
        )
        route53.ARecord(
            self,
            "AliasRecordwww",
            zone=hosted_zone,
            record_name="www." + config["customDomain"],
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
        )

        # Upload local website files to the S3 bucket
        s3deploy.BucketDeployment(
            self,
            "DeployWebsite",
            sources=[s3deploy.Source.asset("./src")],  # Path to your website files
            destination_bucket=bucket,
            distribution=distribution,  # Invalidate CloudFront cache after deployment
            retain_on_delete=False,  # Optional: whether to keep files in S3 when stack is deleted
        )

        # Output the CloudFront distribution domain
        CfnOutput(
            self,
            "CloudFrontDistributionDomainCfn",
            value=distribution.distribution_domain_name,
        )
