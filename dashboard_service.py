import logging
import os
import base64
import time

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
    filename: str
    file: SerializedBase64


class DashboardCapability(IntersectBaseCapabilityImplementation):
    """DashboardCapability"""

    intersect_sdk_capability_name = "NSDFDashboard"

    @intersect_status()
    def status(self) -> str:
        """Basic status function which returns a hard-coded string."""
        return "Up"

    @intersect_message()
    def get_bragg_data(self, bragg_file: FileType) -> None:
        """Endpoint returns a .gsa file with bragg data and writes it to disk."""
        timestamp = int(time.time())
        path = os.path.join("./bragg_data", f"{timestamp}_{bragg_file.filename}")
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "wb") as f:
            bytes_data = base64.decodebytes(bragg_file.file)
            f.write(bytes_data)


def dashboard_service():
    """dashboard_service

    Initializes service to query data for the dashboard (get_bragg_data, get_next_temperature, get_transition_data)
    """
    from_config_file = {
        "brokers": [
            {
                "username": "intersect_username",
                "password": "intersect_password",
                "host": "broker",
                "port": 1883,
                "protocol": "mqtt3.1.1",
            },
        ],
    }
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
