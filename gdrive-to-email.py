import io
import logging
import os.path
import tempfile
import smtplib
import sys
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def main():
    load_environment_variables()
    drive_service = get_drive_service()
    query = f"'{UNSENT_GDRIVE_FOLDER_ID}' in parents AND mimeType='{MIME_MAIN_TYPE}/{MIME_SUB_TYPE}'"

    files = []
    page_token = None
    while True:
        results = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, parents)",
            pageToken=page_token
        ).execute()
        files.extend(results.get('files', []))
        page_token = results.get('nextPageToken', None)
        if page_token is None:
            break

    if not files:
        logger.warning(f"No files found. query={query}")
        exit(0)

    process_files(drive_service, files)
    logger.debug("Done!")


import os
from dotenv import load_dotenv

def load_environment_variables():
    """
    Load environment variables from the .env file.

    This function loads the values of environment variables from the .env file
    using the `dotenv` library. The environment variables are then assigned to
    global variables for later use.

    Args:
        None

    Returns:
        None
    """
    load_dotenv()
    global CREDENTIAL_FILENAME
    global MIME_MAIN_TYPE
    global MIME_SUB_TYPE
    global UNSENT_GDRIVE_FOLDER_ID
    global SENDER_EMAIL
    global SENT_GDRIVE_FOLDER_ID
    global RECEIVER_EMAIL
    global SMTP_SERVER_HOSTNAME
    global SMTP_SERVER_TLS_PORT
    global SMTP_SERVER_SENDER_PASSWORD

    CREDENTIAL_FILENAME = os.getenv("CREDENTIAL_FILENAME")
    MIME_MAIN_TYPE = os.getenv("MIME_MAIN_TYPE")
    MIME_SUB_TYPE = os.getenv("MIME_SUB_TYPE")
    UNSENT_GDRIVE_FOLDER_ID = os.getenv("UNSENT_GDRIVE_FOLDER_ID")
    SENT_GDRIVE_FOLDER_ID = os.getenv("SENT_GDRIVE_FOLDER_ID")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
    SMTP_SERVER_HOSTNAME = os.getenv("SMTP_SERVER_HOSTNAME")
    SMTP_SERVER_TLS_PORT = os.getenv("SMTP_SERVER_TLS_PORT")
    SMTP_SERVER_SENDER_PASSWORD = os.getenv("SMTP_SERVER_SENDER_PASSWORD")


def get_drive_service():
    """
    Returns the Google Drive service object.

    :return: Google Drive service object.
    """
    creds = None
    if os.path.exists(CREDENTIAL_FILENAME):
        creds = Credentials.from_service_account_file(CREDENTIAL_FILENAME)
    else:
        logger.error(f"Cannot find credentials file {CREDENTIAL_FILENAME}. Exiting script.")
        exit(1)

    drive_service = build('drive', 'v3', credentials=creds)
    return drive_service


def process_files(drive_service, files):
    """
    Process a list of files by downloading and moving them.

    Args:
        drive_service (DriveService): The Google Drive service object.
        files (list): A list of file metadata.

    Returns:
        None
    """
    for file_metadata in files:
        download_file(drive_service, file_metadata)
        move_file(drive_service, file_metadata, SENT_GDRIVE_FOLDER_ID)


def download_file(drive_service, file_metadata):
    """
    Downloads a file from Google Drive and sends it as an email attachment.

    Args:
        drive_service (googleapiclient.discovery.Resource): The Google Drive service object.
        file_metadata (dict): The metadata of the file to be downloaded.

    Returns:
        None
    """
    request = drive_service.files().get_media(fileId=file_metadata['id'])
    file_bytes = io.BytesIO()
    downloader = MediaIoBaseDownload(file_bytes, request)
    done = False

    while done is False:
        status, done = downloader.next_chunk()
        logger.info(f"Download {file_metadata['name']} {int(status.progress() * 100)}%.")

    with tempfile.TemporaryFile() as file_object:
        file_object.write(file_bytes.getbuffer())
        file_object.seek(0)
        email_file_as_attachment(file_metadata, file_object)


def email_file_as_attachment(file_metadata, file_object):
    """
    Sends an email with the given file attached as an attachment.

    Args:
        file_metadata (dict): Metadata of the file to be attached.
        file_object (file): File object to be attached.

    Returns:
        None
    """
    subject = f"{file_metadata['name']}"
    body = "Please see attached file."

    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = f"{RECEIVER_EMAIL}"
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))

    part = MIMEBase(MIME_MAIN_TYPE, MIME_SUB_TYPE)
    part.set_payload(file_object.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename={file_metadata['name']}",
    )
    message.attach(part)

    with smtplib.SMTP(SMTP_SERVER_HOSTNAME, SMTP_SERVER_TLS_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SMTP_SERVER_SENDER_PASSWORD)
        server.send_message(message)
        logger.info(f"Email sent successfully for {file_metadata['name']}")


def move_file(drive_service, file_metadata, destination_folder_id):
    """
    Moves a file to a specified destination folder in Google Drive.

    Parameters:
        drive_service (googleapiclient.discovery.Resource): The Google Drive service object.
        file_metadata (dict): Metadata of the file to be moved.
        destination_folder_id (str): ID of the destination folder.

    Returns:
        None
    """
    # Get the current parents of the file
    file = drive_service.files().get(fileId=file_metadata['id'], fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))

    # Update the file's parents to move it to the destination folder
    file = drive_service.files().update(
        fileId=file_metadata['id'],
        addParents=destination_folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()

    logger.info(f"Moved file {file_metadata['name']} to folder {destination_folder_id}")


if __name__ == "__main__":
    main()
