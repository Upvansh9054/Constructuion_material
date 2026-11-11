import logging
from typing import Dict, Optional
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class S3StorageService:
    """Production S3-compatible storage service supporting AWS S3, MinIO, or Cloudflare R2."""

    def __init__(self):
        self.endpoint_url = settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
            use_ssl=settings.S3_USE_SSL,
        )
        self.bucket = settings.S3_BUCKET_NAME

    def ensure_bucket_exists(self) -> None:
        """Create bucket if it does not already exist (primarily for local MinIO testing)."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
                logger.info(f"Bucket {self.bucket} not found. Creating bucket...")
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                    logger.info(f"Bucket {self.bucket} created successfully.")
                except Exception as create_err:
                    logger.warning(f"Could not create bucket: {create_err}")
            else:
                logger.warning(f"S3 head_bucket check failed: {e}")

    def generate_presigned_upload_url(
        self, s3_key: str, content_type: str, expires_in: int = 3600
    ) -> Dict[str, str]:
        """Generate presigned PUT URL for direct client upload."""
        try:
            url = self.client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": s3_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            return {"upload_url": url, "s3_key": s3_key}
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload url: {e}")
            raise

    def generate_presigned_download_url(
        self, s3_key: str, expires_in: int = 3600
    ) -> Optional[str]:
        """Generate presigned GET URL for viewing or downloading images."""
        try:
            url = self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned download url: {e}")
            return None

    def upload_bytes(
        self, data: bytes, s3_key: str, content_type: str = "image/jpeg"
    ) -> str:
        """Upload in-memory bytes directly to S3."""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=data,
                ContentType=content_type,
            )
            return s3_key
        except ClientError as e:
            logger.error(f"Failed to upload bytes to S3: {e}")
            raise

    def download_bytes(self, s3_key: str) -> bytes:
        """Download raw object bytes from S3."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Failed to download object from S3: {e}")
            raise


storage_service = S3StorageService()


def get_storage_service() -> S3StorageService:
    return storage_service
