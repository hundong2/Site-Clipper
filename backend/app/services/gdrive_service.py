from __future__ import annotations

import io
import logging

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_NAME = "SiteClipper"


def _get_or_create_folder(service, folder_name: str) -> str:
    query = (
        f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' "
        "and trashed=false"
    )
    results = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_to_drive(
    access_token: str,
    filename: str,
    content: str,
    folder_name: str = FOLDER_NAME,
) -> dict:
    creds = Credentials(token=access_token)
    service = build("drive", "v3", credentials=creds)

    folder_id = _get_or_create_folder(service, folder_name)

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(
        io.BytesIO(content.encode("utf-8")),
        mimetype="text/markdown",
        resumable=True,
    )
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,name,webViewLink")
        .execute()
    )

    logger.info("Uploaded %s to Drive folder %s", uploaded["name"], folder_name)
    return {
        "file_id": uploaded["id"],
        "name": uploaded["name"],
        "web_link": uploaded.get("webViewLink", ""),
    }
