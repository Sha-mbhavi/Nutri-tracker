import os
import json
from datetime import datetime
from flask import current_app

class AzureBlobService:
    """
    DP-900 Cloud Non-Relational Storage Integration
    Connects to Azure Blob Storage for storing unstructured documents, exported reports,
    and semi-structured JSON telemetry. Gracefully falls back to local instance archive
    when running in offline/local development mode.
    """

    def __init__(self, container_name="nutrition-reports"):
        self.container_name = container_name
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    def upload_blob(self, filename, data, content_type="application/octet-stream"):
        """
        Uploads content to Azure Blob Storage container.
        Returns a dict containing blob metadata, URI, and storage mode.
        """
        if isinstance(data, str):
            data_bytes = data.encode("utf-8")
        else:
            data_bytes = data

        size_bytes = len(data_bytes)
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Check if production Azure Blob credentials are provided
        if self.connection_string and "DefaultEndpointsProtocol" in self.connection_string:
            try:
                from azure.storage.blob import BlobServiceClient, ContentSettings
                service_client = BlobServiceClient.from_connection_string(self.connection_string)
                container_client = service_client.get_container_client(self.container_name)
                if not container_client.exists():
                    container_client.create_container()
                blob_client = container_client.get_blob_client(filename)
                blob_client.upload_blob(
                    data_bytes,
                    overwrite=True,
                    content_settings=ContentSettings(content_type=content_type)
                )
                return {
                    "success": True,
                    "storage_provider": "Azure Blob Storage (Cloud Production)",
                    "container": self.container_name,
                    "filename": filename,
                    "uri": blob_client.url,
                    "size_bytes": size_bytes,
                    "timestamp": timestamp,
                    "status": "Uploaded to Azure Cloud Container"
                }
            except Exception as e:
                # Log error and fall back to local instance storage
                current_app.logger.warning(f"Azure upload fallback: {e}")

        # Local development / offline fallback storage
        local_dir = os.path.join(current_app.instance_path, "blob_storage", self.container_name)
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, filename)

        with open(local_path, "wb") as f:
            f.write(data_bytes)

        simulated_cloud_url = f"https://nutritrackstorage.blob.core.windows.net/{self.container_name}/{filename}"

        return {
            "success": True,
            "storage_provider": "Azure Blob Storage (Local Simulation / Dev Mode)",
            "container": self.container_name,
            "filename": filename,
            "uri": simulated_cloud_url,
            "local_path": local_path,
            "size_bytes": size_bytes,
            "timestamp": timestamp,
            "status": "Archived successfully"
        }

blob_service = AzureBlobService()
