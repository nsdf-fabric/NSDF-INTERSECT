"""
File: dashboard_service.py
Author: NSDF-INTERSECT Team
License: BSD-3
Description: The service component. It uses intersect-sdk to get all messages from the broker.
"""

import logging
import os
import base64
import time
from typing import List
import yaml
import uuid
from constants import (
    BRAGG_DATA_VOLUME,
    INTERSECT_SERVICE_CONFIG,
    TRANSITION_DATA_VOLUME,
    ANDIE_DATA_VOLUME,
    SCIENTIST_CLOUD_VOLUME,
)

from intersect_sdk import (
    HierarchyConfig,
    IntersectBaseCapabilityImplementation,
    IntersectService,
    IntersectServiceConfig,
    intersect_message,
    intersect_status,
)
from typing_extensions import Annotated
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SerializedBase64 = Annotated[bytes, Field(json_schema_extra={"format": "base64"})]


class FileType(BaseModel):
    """
    Represents a gsa file.

    Attributes:
        filename (str): The name of the file.
        file (SerializedBase64): The file content serialized in Base64 format.
    """

    filename: str
    file: SerializedBase64


class TransitionData(BaseModel):
    """
    Represents a transition data record.

    Attributes:
        id (str): The campaign id for the transition data record.
        temp (float): The temperature value associated with the transition.
        ylist (List[float]): A list of float values representing the observed peaks (d-Spacing) associated with temp.
    """

    id: str
    temp: float
    ylist: List[float]


class NextTemperature(BaseModel):
    """
    Represents the next temperature record (ANDiE prediction).

    Attributes:
        id (str): The campaign id for the next temperature data record.
        data (float): The predicted temperature value.
        timestamp (int): The timestamp when the prediction was recorded.
    """

    id: str
    data: float
    timestamp: int


def last_record(cid: str) -> TransitionData:
    """
    Retrieve the last record from the transition file for the given cid.

    Args:
        cid (str): The campaign ID.

    Returns:
        TransitionData: The last transition data record.

    Raises:
        OSError: If an error occurs while retrieving the last record on the file.
    """
    transition_state_path = os.path.join(
        TRANSITION_DATA_VOLUME, f"{cid}_transition.txt"
    )
    tdata = TransitionData(id="", temp=0, ylist=[])
    if not os.path.exists(transition_state_path):
        return tdata

    with open(transition_state_path, "rb") as f:
        try:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b"\n":
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            raise OSError(
                f"file: {transition_state_path} failed to process the last record"
            )

        last_measure = f.readline().decode()
        if last_measure == "":
            return tdata

        fields = last_measure.split(",")
        tdata.id = fields[0]
        tdata.temp = float(fields[1])
        tdata.ylist = [float(y) for y in fields[2:]]
        return tdata


def isValidTransitionRecord(prev: TransitionData, new: TransitionData) -> bool:
    """
    Checks if a received TransitionData is a valid record.

    Args:
        prev(TransitionData): The latest TransitionData record.
        new(TransitionData): The received TransitionData record.

    Returns:
        bool: True, if it is a valid record. Otherwise, False.

    """
    return prev.id == new.id and len(prev.ylist) == len(new.ylist)


class DashboardCapability(IntersectBaseCapabilityImplementation):
    """DashboardCapability"""

    intersect_sdk_capability_name = "NSDFDashboard"

    @intersect_status()
    def status(self) -> str:
        """Basic status function which returns a hard-coded string."""
        return "Up"

    @intersect_message()
    def get_bragg_data(self, bragg_file: FileType) -> None:
        """
        Endpoint to return a .gsa file with bragg data

        Args:
            bragg_file(FileType): the gsa file to process

        Side Effects:
            - Creates the bragg volume, if it does not exists
            - Creates the scientist cloud volume, if it does not exists
            - writes the file to the ephemeral bragg volume (stateless)
            - writes the file to the scientist cloud volume (stateful)
        """
        timestamp = int(time.time())
        path = os.path.join(BRAGG_DATA_VOLUME, f"{timestamp}_{bragg_file.filename}")
        storage_path = os.path.join(
            SCIENTIST_CLOUD_VOLUME, f"{timestamp}_{bragg_file.filename}"
        )

        os.makedirs(os.path.dirname(path), exist_ok=True)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        with open(path, "wb") as f, open(storage_path, "wb") as s:
            bytes_data = base64.decodebytes(bragg_file.file)
            f.write(bytes_data)
            s.write(bytes_data)

    @intersect_message()
    def get_transition_data_single(self, transition_data: TransitionData) -> None:
        """
        Endpoint to return the next point in the transition plot

        Args:
            transition_data(TransitionData): the next transition data to process in the campaign

        Side Effects:
            - Creates the transition volume, if it does not exists
            - Creates the scientist cloud volume, if it does not exists
            - writes the file to the ephemeral transition volume (stateless)
            - writes the file to the scientist cloud volume (stateful)
        """

        file_id = f"{transition_data.id}_transition.txt"
        ephemeral_vol_path = os.path.join(TRANSITION_DATA_VOLUME, file_id)
        storage_path = os.path.join(SCIENTIST_CLOUD_VOLUME, file_id)
        os.makedirs(os.path.dirname(ephemeral_vol_path), exist_ok=True)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        try:
            latest_record = last_record(file_id)
            ylist = ",".join(map(str, transition_data.ylist))

            if latest_record.id == "" or isValidTransitionRecord(
                latest_record, transition_data
            ):
                with open(ephemeral_vol_path, "a") as e, open(storage_path, "a") as s:
                    e.write(f"{uuid.uuid4()},{transition_data.temp},{ylist}\n")
                    s.write(f"{uuid.uuid4()},{transition_data.temp},{ylist}\n")
        except Exception as e:
            logger.error(e)

    @intersect_message()
    def get_next_temperature(self, next_temperature: NextTemperature) -> None:
        """
        Endpoint to return the ANDiE next temperature

        Args:
            next_temperature(NextTemperature): the next temperature to process in the campaign

        Side Effects:
            - Creates the next temperature volume, if it does not exists
            - Creates the scientist cloud volume, if it does not exists
            - writes the file to the ephemeral next temperature volume (stateless)
            - writes the file to the scientist cloud volume (stateful)

        """
        ephemeral_vol_path = os.path.join(ANDIE_DATA_VOLUME, "andie.txt")
        storage_path = os.path.join(SCIENTIST_CLOUD_VOLUME, "andie.txt")
        os.makedirs(os.path.dirname(ephemeral_vol_path), exist_ok=True)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        with open(ephemeral_vol_path, "a") as e, open(storage_path, "a") as s:
            e.write(
                f"{next_temperature.id},{uuid.uuid4()},{next_temperature.timestamp},{next_temperature.data}\n"
            )
            s.write(
                f"{next_temperature.id},{uuid.uuid4()},{next_temperature.timestamp},{next_temperature.data}\n"
            )


def dashboard_service():
    """
    Initializes service to query data for the dashboard.
    """
    from_config_file = {}
    config_path = os.getenv(INTERSECT_SERVICE_CONFIG, "/app/config_default.yaml")
    with open(config_path) as f:
        from_config_file = yaml.safe_load(f)

    config = IntersectServiceConfig(
        hierarchy=HierarchyConfig(
            organization="nsdf-organization",
            facility="nsdf-facility",
            system="nsdf-system",
            subsystem="nsdf-subsystem",
            service="nsdf-dashboard-service",
        ),
        **from_config_file,
    )

    capability = DashboardCapability()
    service = IntersectService([capability], config)

    logger.info("Starting dashboard_service")
    return service


if __name__ == "__main__":
    svc = dashboard_service()
    svc.startup()
