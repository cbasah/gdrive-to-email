# GDrive-to-Email

This simple Python script checks a Google Drive folder for files matching a given MIME-type, sends an e-mail with each file as an attachment and moves the file to another Google Drive folder after the e-mail is sent.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install -r requirements.txt
```

Create a Google Cloud service account and generate the JSON credentials file (e.g. credentials.json). Store the credentials file at the root folder of this project.

Generate `.env` file with the following environment variables. The following values are just examples.

```
CREDENTIAL_FILENAME = "credentials.json"
MIME_MAIN_TYPE = "application"
MIME_SUB_TYPE = "pdf"
SENT_GDRIVE_FOLDER_ID = "1NMsA0ssdw2q3jVD1OMwhaaansNO2mzxxx"
UNSENT_GDRIVE_FOLDER_ID = "1A9l0jRnd415c2h4fpBy57333tiRuHzzz"
SENDER_EMAIL = "sender@senderdomain.com"
RECEIVER_EMAIL = "receiver@receiver@gmail.com"
SMTP_SERVER_HOSTNAME = "smtp.gmail.com"
SMTP_SERVER_TLS_PORT = 587
SMTP_SERVER_SENDER_PASSWORD = "abcd efgh ijkl mnop"
```

PRs are welcomed!
