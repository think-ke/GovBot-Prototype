"""
Minio Storage Utilities

This module provides functionality for interacting with MinIO object storage,
including initializing the client, uploading documents, and retrieving them.
"""

import os
from typing import BinaryIO, Optional, Dict, List, Tuple
from datetime import timedelta
import logging
from minio import Minio
from minio.error import S3Error
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class MinioClient:
    """Client for interacting with MinIO object storage."""
    
    def __init__(self):
        """Initialize the MinIO client using environment variables."""
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost")
        self.port = int(os.getenv("MINIO_PORT", "9000"))
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "govstack-docs")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.client = self._initialize_client()
        self._ensure_bucket_exists()
    
    def _initialize_client(self) -> Minio:
        """Create and return a Minio client instance."""
        try:
            server = f"{self.endpoint}:{self.port}"
            logger.info(f"Initializing MinIO client with endpoint: {server}")
            return Minio(
                server,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise
    
    def _ensure_bucket_exists(self) -> None:
        """Ensure the specified bucket exists, creating it if necessary."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                logger.info(f"Creating bucket: {self.bucket_name}")
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket created: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error checking/creating bucket: {str(e)}")
            raise
    
    def upload_file(self, file_obj: BinaryIO, object_name: str, 
                   content_type: str = "application/octet-stream",
                   metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Upload a file to MinIO storage.
        
        Args:
            file_obj: File-like object to upload
            object_name: Name to give the object in storage
            content_type: MIME type of the file
            metadata: Optional metadata to attach to the object
            
        Returns:
            Object name of the uploaded file
        """
        try:
            logger.info(f"Uploading file to bucket {self.bucket_name} with name {object_name}")
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_obj,
                length=-1,  # Calculate length automatically
                content_type=content_type,
                metadata=metadata
            )
            logger.info(f"File uploaded successfully: {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Error uploading file {object_name}: {str(e)}")
            raise
    
    def get_file(self, object_name: str) -> Tuple[BinaryIO, Dict]:
        """
        Retrieve a file from MinIO storage.
        
        Args:
            object_name: Name of the object to retrieve
            
        Returns:
            Tuple of (file data as stream, metadata)
        """
        try:
            logger.info(f"Retrieving file from bucket {self.bucket_name}: {object_name}")
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            # Get metadata
            stat = self.client.stat_object(self.bucket_name, object_name)
            metadata = stat.metadata if hasattr(stat, 'metadata') else {}
            
            return response, metadata
        except S3Error as e:
            logger.error(f"Error retrieving file {object_name}: {str(e)}")
            raise
    
    def delete_file(self, object_name: str) -> None:
        """
        Delete a file from MinIO storage.
        
        Args:
            object_name: Name of the object to delete
        """
        try:
            logger.info(f"Deleting file from bucket {self.bucket_name}: {object_name}")
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"File deleted successfully: {object_name}")
        except S3Error as e:
            logger.error(f"Error deleting file {object_name}: {str(e)}")
            raise
    
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access to an object.
        
        Args:
            object_name: Name of the object to generate URL for
            expires: Expiry time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string
        """
        try:
            logger.info(f"Generating presigned URL for {object_name}")
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL for {object_name}: {str(e)}")
            raise
    
    def list_files(self, prefix: str = None, recursive: bool = True) -> List[Dict]:
        """
        List files in the storage bucket.
        
        Args:
            prefix: Optional prefix to filter objects
            recursive: Whether to list objects recursively in directories
            
        Returns:
            List of object information dictionaries
        """
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name, 
                prefix=prefix,
                recursive=recursive
            )
            
            result = []
            for obj in objects:
                result.append({
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified
                })
            
            return result
        except S3Error as e:
            logger.error(f"Error listing files: {str(e)}")
            raise


# Create a singleton instance for reuse
minio_client = MinioClient()