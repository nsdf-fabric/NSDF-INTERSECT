import pathlib
import dotenv
import os
from botocore.client import Config
from botocore.exceptions import ClientError
import boto3
import time
import logging
import subprocess
import random
import concurrent.futures
from constants import BUCKET_PATH, BRAGG_PATH, SCIENTIST_CLOUD_VOLUME, STORAGE_SCAN_PERIOD, STATE_VOLUME, RETRY_FILE


logging.basicConfig(level=logging.INFO)
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


def upload_with_retry(local_filepath, key, max_retries=5, delay=2) -> str:
    retries = 0
    bucket = get_bucket()
    cksum = int(Shell(f"cksum {local_filepath}").split()[0].strip())
    filename = os.path.basename(local_filepath)
    while retries < max_retries:
        try:
            bucket.upload_file(
                local_filepath,
                key,
                ExtraArgs={"Metadata": {"checksum": str(cksum)}},
            )
            return filename
        except Exception:
            retries += 1
            if retries < max_retries:
                # Randomize the delay a bit to avoid retry storms
                time.sleep(delay + random.uniform(0, 1))
            else:
                # write to retry.txt to upload later
                path = os.path.join(STATE_VOLUME, RETRY_FILE)
                os.makedirs(path, exist_ok=True)
                with open(path, "a") as f:
                    f.write(f"{os.path.basename(local_filepath)}\n")

                raise Exception(f"Failed to upload {filename}, after {max_retries} retries")

    return filename


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


def main():
    logger.info("Starting Storage Service")

    if not os.path.exists(SCIENTIST_CLOUD_VOLUME):
        os.makedirs(SCIENTIST_CLOUD_VOLUME, exist_ok=True)

    while True:
        files = os.listdir(SCIENTIST_CLOUD_VOLUME)
        jobs = []
        if files:
            for file in files:
                match pathlib.Path(file).suffix:
                    case ".gsa":
                        key = os.path.join(BUCKET_PATH, BRAGG_PATH, file)
                        if not check_if_key_exists(key):
                            local_filepath = os.path.join(SCIENTIST_CLOUD_VOLUME, file)
                            jobs.append([upload_with_retry, local_filepath, key])
                    case _:
                        logger.warning(f"unsupported file type: {file}")
                        continue

            with concurrent.futures.ThreadPoolExecutor(max_workers=32) as ex:
                futures = [ex.submit(*job) for job in jobs]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        logger.info(f"Uploaded file {result}")
                    except Exception as e:
                        logger.error(e)

        time.sleep(STORAGE_SCAN_PERIOD)


if __name__ == "__main__":
    main()
