import logging
import os
import base64
import time
from typing import List, Tuple
import yaml
import uuid
from constants import (
    BRAGG_VOLUME,
    SCIENTIST_CLOUD_VOLUME,
    STATE_VOLUME,
    TRANSITION_DATA_FILE,
    ANDIE_DATA_FILE,
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


CONFIG_SERVICE = "config_service.yaml"

SerializedBase64 = Annotated[bytes, Field(json_schema_extra={"format": "base64"})]


class FileType(BaseModel):
    filename: str
    file: SerializedBase64


class TransitionFile(BaseModel):
    filename: str
    data: List[Tuple[float, float, float]]


class TransitionPoint(BaseModel):
    data: Tuple[float, float, float]


class NextTemperature(BaseModel):
    data: float
    timestamp: int


class DashboardCapability(IntersectBaseCapabilityImplementation):
    """DashboardCapability"""

    intersect_sdk_capability_name = "NSDFDashboard"

    @intersect_status()
    def status(self) -> str:
        """Basic status function which returns a hard-coded string."""
        return "Up"

    @intersect_message()
    def get_bragg_data(self, bragg_file: FileType) -> None:
        """get_bragg_data
        Endpoint to return a .gsa file with bragg data
        """
        timestamp = int(time.time())
        path = os.path.join(BRAGG_VOLUME, f"{timestamp}_{bragg_file.filename}")
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
    def get_transition_data(self, transition_file: TransitionFile) -> None:
        """get_transition_data
        Endpoint to return an entire transition plot measurement
        """

        storage_path = os.path.join(STATE_VOLUME, TRANSITION_DATA_FILE)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        with open(storage_path, "a") as s:
            for data_tuple in transition_file.data:
                temp, peak1, peak2 = data_tuple
                s.write(f"{uuid.uuid4()},{temp},{peak1},{peak2}\n")

    @intersect_message()
    def get_transition_data_single(self, transition_point: TransitionPoint) -> None:
        """get_transition_data_single
        Endpoint to return the next point in the transition plot
        """

        storage_path = os.path.join(STATE_VOLUME, TRANSITION_DATA_FILE)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        temp, peak1, peak2 = transition_point.data
        with open(storage_path, "a") as s:
            s.write(f"{uuid.uuid4()},{temp},{peak1},{peak2}\n")

    @intersect_message()
    def get_next_temperature(self, next_temperature: NextTemperature) -> None:
        """get_next_temperature
        Endpoint to return the ANDiE next temperature
        """
        storage_path = os.path.join(STATE_VOLUME, ANDIE_DATA_FILE)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        with open(storage_path, "a") as s:
            s.write(
                f"{uuid.uuid4()},{next_temperature.timestamp},{next_temperature.data}\n"
            )


def dashboard_service():
    """dashboard_service

    Initializes service to query data for the dashboard (get_bragg_data, get_next_temperature, get_transition_data)
    """
    from_config_file = {}
    with open(CONFIG_SERVICE) as f:
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
