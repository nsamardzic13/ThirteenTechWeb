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

        # Create an S3 bucket for static website hosting
        bucket = s3.Bucket(
            self,
            "StaticWebsiteBucket",
            bucket_name=config["bucketName"],
            website_index_document="index.html",
            public_read_access=False,  # Disable direct public access, will use CloudFront
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,  # Destroy bucket on stack deletion
        )

        # Create a Route53 hosted zone (or use an existing one)
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=config["customDomain"]  # Your custom domain
        )

        # Create an ACM certificate for HTTPS
        certificate = acm.Certificate(
            self,
            "WebsiteCertificate",
            domain_name=config["customDomain"],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # Create a CloudFront distribution with the S3 bucket as the origin
        distribution = cloudfront.Distribution(
            self,
            "CloudFrontDistribution",
            default_root_object="index.html",
            domain_names=[config["customDomain"]],
            certificate=certificate,  # Associate the ACM certificate with the distribution
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin(bucket),  # Use S3BucketOrigin instead of S3Origin
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,  # Ensure HTTPS
            ),
        )

        # Add an A record in Route53 pointing to the CloudFront distribution
        route53.ARecord(
            self,
            "AliasRecord",
            zone=hosted_zone,
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
            "CloudFrontDistributionDomain",
            value=distribution.distribution_domain_name,
            description="The CloudFront distribution domain name",
        )

        # Output the custom domain
        CfnOutput(
            self,
            "CustomDomain",
            value=f"https://{config['customDomain']}",
            description="Custom domain for the static website",
        )
