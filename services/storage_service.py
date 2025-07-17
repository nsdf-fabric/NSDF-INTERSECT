"""
File: storage_service.py
Authors: NSDF-INTERSECT Team
License: BSD-3
Description: The storage component exports data to the ScientistCloud
and serves as the caching layer for stateful features.
"""

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
import yaml


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="nsdf-intersect-storage.log", encoding="utf-8", level=logging.INFO
)


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
        s3.Object(key).load()
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        # other error
        return False


def upload_with_retry(local_filepath, key, config, max_retries=5, delay=2) -> str:
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
                path = os.path.join(
                    config["volumes"]["scientist_cloud_volume"], "retry.txt"
                )
                os.makedirs(path, exist_ok=True)
                with open(path, "a") as f:
                    f.write(f"{os.path.basename(local_filepath)}\n")

                raise Exception(
                    f"Failed to upload {filename}, after {max_retries} retries"
                )

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
    config = {}
    config_path = os.getenv("INTERSECT_STORAGE_CONFIG", "/app/config_storage.yaml")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(
            f"could not initialize storage service, configuration path of storage does not exists: {e}"
        )
        return

    logger.info("Starting Storage Service")

    while True:
        files = os.listdir(config["volumes"]["scientist_cloud_volume"])
        jobs = []
        if files:
            for file in files:
                path = pathlib.Path(file)
                ext = path.suffix
                if ext == ".gsa":
                    key = os.path.join(
                        config["sci_cloud"]["bucket_prefix"],
                        config["sci_cloud"]["bragg_prefix"],
                        file,
                    )
                    if not check_if_key_exists(key):
                        local_filepath = os.path.join(
                            config["volumes"]["scientist_cloud_volume"], file
                        )
                        jobs.append([upload_with_retry, local_filepath, key, config])
                elif ext == ".done":
                    file = f"{path.stem}_transition.txt"
                    key = os.path.join(
                        config["sci_cloud"]["bucket_prefix"],
                        config["sci_cloud"]["transition_prefix"],
                        file,
                    )
                    if not check_if_key_exists(key):
                        local_filepath = os.path.join(
                            config["volumes"]["scientist_cloud_volume"], file
                        )
                        jobs.append([upload_with_retry, local_filepath, key, config])
                else:
                    continue

            with concurrent.futures.ThreadPoolExecutor(max_workers=32) as ex:
                futures = [ex.submit(*job) for job in jobs]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if pathlib.Path(result).suffix == ".txt":
                            os.remove(
                                os.path.join(
                                    config["volumes"]["scientist_cloud_volume"],
                                    f"{result.split('_')[0]}.done",
                                )
                            )
                        logger.info(f"Uploaded file {result}")
                    except Exception as e:
                        logger.error(e)

        time.sleep(config["scan_period"])


if __name__ == "__main__":
    main()
