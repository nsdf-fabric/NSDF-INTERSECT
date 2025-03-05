import pathlib
import dotenv
import signal
import os
from botocore.client import Config
from botocore.exceptions import ClientError
import boto3
import time
import logging
import subprocess
import random
import sys

PREFIX = "utk"
STORAGE_VOLUME = "./scientist_cloud_volume"
RETRY_VOLUME = " ./retry_volume"
RETRY_FILE = "retry.txt"
BUCKET_PATH = "utk"
BRAGG_PATH = "bragg_data"
TRANSITION_DATA_PATH = "transition_data"
NEXT_TEMPERATURE_DATA_PATH = "next_temperature_data"
SCAN_PERIOD = 60

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def Shell(cmd):
    return subprocess.check_output(cmd, shell=True, text=True)


def check_if_key_exists(key: str) -> bool:
    """
    Check if a given key exists in the bucket
    ----
    Return
    bool: True if the key is in the bucket, False otherwise
    """
    if key == "":
        return False

    s3 = get_bucket()
    try:
        obj = s3.Object(key)
        obj.load()
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        # other error
        return False


def upload_with_retry(local_filepath, key, cksum, max_retries=5, delay=2):
    retries = 0
    bucket = get_bucket()
    while retries < max_retries:
        try:
            bucket.upload_file(
                local_filepath,
                key,
                ExtraArgs={"Metadata": {"checksum": str(cksum)}},
            )
            return True
        except Exception:
            retries += 1
            if retries < max_retries:
                # Randomize the delay a bit to avoid retry storms
                time.sleep(delay + random.uniform(0, 1))
            else:
                # write to retry.txt to upload later
                path = os.path.join(RETRY_VOLUME, RETRY_FILE)
                os.makedirs(path, exist_ok=True)
                with open(path, "a") as f:
                    f.write(f"{os.path.basename(local_filepath)}\n")

                return False


def get_bucket():
    dotenv.load_dotenv()
    endpoint_url = os.getenv("ENDPOINT_URL")
    bucket_name = os.getenv("BUCKET_NAME")
    aws_access_key_id = os.getenv("ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("SECRET_ACCESS_KEY")

    config = Config(signature_version="s3v4")
    s3 = boto3.resource(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        config=config,
        verify=True,
    )
    bucket = s3.Bucket(bucket_name)
    return bucket


def signal_handler(_sig, _frame):
    logger.info("Stopping storage service...")
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, signal_handler)
    logger.info("Starting Storage Service")

    if not os.path.exists(STORAGE_VOLUME):
        os.makedirs(STORAGE_VOLUME, exist_ok=True)

    while True:
        files = os.listdir(STORAGE_VOLUME)
        if files:
            for file in files:
                subfolder = ""
                match pathlib.Path(file).suffix:
                    case ".gsa":
                        subfolder = BRAGG_PATH
                    case ".txt":
                        if "ANDiE" in file:
                            subfolder = NEXT_TEMPERATURE_DATA_PATH
                        else:
                            subfolder = TRANSITION_DATA_PATH
                    case _:
                        continue

                key = os.path.join(PREFIX, subfolder, file)
                if not check_if_key_exists(key):
                    local_filepath = os.path.join(STORAGE_VOLUME, file)
                    cksum = int(Shell(f"cksum {local_filepath}").split()[0].strip())
                    success = upload_with_retry(local_filepath, key, cksum)
                    if success:
                        logger.info(f"Uploaded {file}")
                    else:
                        logger.error(f"Failed to upload {file}")

        time.sleep(SCAN_PERIOD)


if __name__ == "__main__":
    main()
