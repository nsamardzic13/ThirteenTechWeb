import json
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

# Load the configuration from a JSON file
with open('config.json', 'r') as f:
    config = json.load(f)

class ThirteenTechWebStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an S3 bucket for static website hosting with public access
        bucket = s3.Bucket(self, "StaticWebsiteBucket",
            bucket_name=config['bucketName'],
            website_index_document="index.html",  # Index document
            public_read_access=True,              # Enable public access
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,  # Allow public access but block ACLs
            removal_policy=RemovalPolicy.DESTROY, # Destroy bucket on stack deletion
        )

        # Upload local website files to the S3 bucket
        s3deploy.BucketDeployment(self, "DeployWebsite",
            sources=[s3deploy.Source.asset("./src")],  # Path to your website files
            destination_bucket=bucket,
            retain_on_delete=False,  # Optional: whether to keep files in S3 when stack is deleted
        )

        # Output the S3 website URL
        CfnOutput(self, "BucketWebsiteURL",
            value=bucket.bucket_website_url,
            description="URL for the static website hosted in S3"
        )
