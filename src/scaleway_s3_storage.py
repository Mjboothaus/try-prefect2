# Scaleway S3 storage
# Credentials stored in `settings.toml` and `.secrets.toml`
# Note: the `Bucket Visibility` is set to public (which specifies whether the list of 
#       objects in the bucket is publicly visible or not; it does not affect the visibility
#       of objects themselves - a file (object) uploaded to a public bucket is private by default).

import io
import logging
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from config import settings

ACCESS_KEY_ID = settings.ACCESS_KEY_ID
STORAGE_BUCKET_NAME = settings.STORAGE_BUCKET_NAME
DEFAULT_ACL = settings.DEFAULT_ACL
REGION_NAME = settings.REGION_NAME
ENDPOINT_URL = settings.ENDPOINT_URL

SECRETS_FILE = ".secrets.toml"
if (
    Path(SECRETS_FILE).exists() is True
    or Path(f'../{SECRETS_FILE}').exists() is True  # if being run from notebooks subdirectory
):    # if there is a local secrets file
    SECRET_ACCESS_KEY = settings.SCALEWAY_SECRET_ACCESS_KEY
else:                                      # use environment variables (deployed on Streamlit Sharing)
    SECRET_ACCESS_KEY = os.environ["SCALEWAY_SECRET_ACCESS_KEY"]


def connect_to_s3():
    return boto3.client(
        "s3",
        region_name=REGION_NAME,
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
    )


def download_s3_file(s3, local_filename, bucket_name, s3_filename):
    with open(local_filename, "wb") as local_filename:
        s3.download_fileobj(bucket_name, s3_filename, local_filename)
        return Path(local_filename.name)


def upload_file_to_s3(s3, file_name, bucket_name, object_name=None):
    """Upload a file to an S3 bucket
    :param file_name: File to upload
    :param bucket_name: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    try:
        response = s3.upload_file(file_name, bucket_name, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

# c.f. https://towardsdatascience.com/reading-and-writing-files-from-to-amazon-s3-with-pandas-ccaf90bfe86c

def dataframe_to_csv_s3(s3, df, bucket_name, filename):
    with io.StringIO() as csv_buffer:
        df.to_csv(csv_buffer, index=False)
        response = s3.put_object(
            Bucket=bucket_name, Key=filename, Body=csv_buffer.getvalue()
        )
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status == 200:
            return True
            #print(f"Successful S3 put_object response. Status - {status}")
        else:
            #print(f"Unsuccessful S3 put_object response. Status - {status}")
            return False
