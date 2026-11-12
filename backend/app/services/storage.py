import logging
import os
from pathlib import Path
from typing import Dict, Optional
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError
from app.core.config import settings

logger = logging.getLogger(__name__)


class S3StorageService:
    """
    Production S3-compatible storage service supporting AWS S3, MinIO, or Cloudflare R2,
    with an automatic local filesystem fallback for development or offline testing.
    """

    def __init__(self):
        self.endpoint_url = settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None
        self.bucket = settings.S3_BUCKET_NAME
        self.local_storage_dir = Path("uploads")
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)
        self.s3_available = True

        try:
            self.client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                config=Config(signature_version="s3v4", connect_timeout=0.5, read_timeout=0.5, retries={"max_attempts": 0}),
                use_ssl=settings.S3_USE_SSL,
            )
        except Exception as e:
            logger.warning(f"S3 client initialization notice (falling back to local disk): {e}")
            self.s3_available = False
            self.client = None

    def ensure_bucket_exists(self) -> None:
        """Create bucket if it does not already exist, or ensure local storage directory."""
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)
        if not self.s3_available or not self.client:
            return

        try:
            self.client.head_bucket(Bucket=self.bucket)
        except (ClientError, EndpointConnectionError, Exception) as e:
            error_code = e.response.get("Error", {}).get("Code") if isinstance(e, ClientError) else None
            if error_code in ("404", "NoSuchBucket"):
                logger.info(f"Bucket {self.bucket} not found. Creating bucket...")
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                    logger.info(f"Bucket {self.bucket} created successfully.")
                    return
                except Exception as create_err:
                    logger.warning(f"Could not create bucket: {create_err}")
            logger.info(f"S3 endpoint unreachable: {e}. Seamless local filesystem fallback engaged.")
            self.s3_available = False

    def generate_presigned_upload_url(
        self, s3_key: str, content_type: str, expires_in: int = 3600
    ) -> Dict[str, str]:
        """Generate presigned PUT URL for direct client upload."""
        if self.s3_available and self.client:
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
            except Exception as e:
                logger.warning(f"Presigned URL generation fallback: {e}")
                self.s3_available = False

        # Local fallback mock upload URL
        return {
            "upload_url": f"/api/v1/surveys/upload-fallback?key={s3_key}",
            "s3_key": s3_key,
        }

    def generate_presigned_download_url(
        self, s3_key: str, expires_in: int = 3600
    ) -> Optional[str]:
        """Generate presigned GET URL for viewing or downloading images."""
        if self.s3_available and self.client:
            try:
                url = self.client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": self.bucket, "Key": s3_key},
                    ExpiresIn=expires_in,
                )
                return url
            except Exception as e:
                logger.debug(f"Presigned download URL generation fallback: {e}")
                self.s3_available = False

        # Fallback to backend media stream endpoint
        return f"/api/v1/surveys/media-file?key={s3_key}"

    def upload_bytes(
        self, data: bytes, s3_key: str, content_type: str = "image/jpeg"
    ) -> str:
        """Upload in-memory bytes to S3, with automatic transparent local disk fallback."""
        if self.s3_available and self.client:
            try:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=data,
                    ContentType=content_type,
                )
                return s3_key
            except Exception as e:
                logger.info(f"S3 put_object unreachable ({e}). Circuit breaker active: routing to local storage.")
                self.s3_available = False

        # Local disk fallback
        local_target = self.local_storage_dir / s3_key
        local_target.parent.mkdir(parents=True, exist_ok=True)
        with open(local_target, "wb") as f:
            f.write(data)
        return s3_key
        local_target = self.local_storage_dir / s3_key
        local_target.parent.mkdir(parents=True, exist_ok=True)
        with open(local_target, "wb") as f:
            f.write(data)
        return s3_key

    def download_bytes(self, s3_key: str) -> bytes:
        """Download raw object bytes from S3 or local disk fallback."""
        # Check local storage first
        local_target = self.local_storage_dir / s3_key
        if local_target.exists():
            with open(local_target, "rb") as f:
                return f.read()

        if self.client:
            try:
                response = self.client.get_object(Bucket=self.bucket, Key=s3_key)
                return response["Body"].read()
            except Exception as e:
                logger.error(f"Failed to download object from S3: {e}")
                raise

        raise FileNotFoundError(f"Media file '{s3_key}' not found in S3 or local storage.")

    def delete_object(self, s3_key: str) -> bool:
        """Delete an object from S3 and local disk storage."""
        deleted = False
        local_target = self.local_storage_dir / s3_key
        if local_target.exists():
            try:
                os.remove(local_target)
                deleted = True
            except Exception as e:
                logger.warning(f"Failed to remove local file {local_target}: {e}")

        if self.client:
            try:
                self.client.delete_object(Bucket=self.bucket, Key=s3_key)
                deleted = True
            except Exception as e:
                logger.warning(f"Failed to delete S3 object {s3_key}: {e}")

        return deleted


storage_service = S3StorageService()


def get_storage_service() -> S3StorageService:
    return storage_service

