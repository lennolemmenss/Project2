from minio import Minio
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000") # MinIO server address
MINIO_ACCESS_KEY = "minioadmin"    # MinIO access key
MINIO_SECRET_KEY = "minioadmin"    # MinIO secret key
MINIO_BUCKET_NAME = "gene-data"    # MinIO bucket name

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set to True if using HTTPS
)

# Ensure the bucket exists
def ensure_bucket_exists():
    if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
        minio_client.make_bucket(MINIO_BUCKET_NAME)
        logger.info(f"Created MinIO bucket: {MINIO_BUCKET_NAME}")

# Upload a file to MinIO
def upload_to_minio(file_path, object_name):
    try:
        minio_client.fput_object(
            MINIO_BUCKET_NAME,
            object_name,
            file_path
        )
        logger.info(f"Uploaded {file_path} to MinIO as {object_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {file_path} to MinIO: {str(e)}")
        return False

# Delete a file from MinIO
def delete_from_minio(object_name):
    try:
        minio_client.remove_object(MINIO_BUCKET_NAME, object_name)
        logger.info(f"Deleted {object_name} from MinIO")
        return True
    except Exception as e:
        logger.error(f"Failed to delete {object_name} from MinIO: {str(e)}")
        return False

# Download file from MinIO
def download_from_minio(object_name, file_path):
    try:
        minio_client.fget_object(
            MINIO_BUCKET_NAME,
            object_name,
            file_path
        )
        logger.info(f"Downloaded {object_name} from MinIO to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {object_name}: {str(e)}")
        return False