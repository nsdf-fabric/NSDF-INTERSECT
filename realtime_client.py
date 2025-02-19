import base64
import logging
import time
import os

from intersect_sdk import (
    INTERSECT_JSON_VALUE,
    IntersectClient,
    IntersectClientCallback,
    IntersectClientConfig,
    IntersectDirectMessageParams,
    default_intersect_lifecycle_loop,
)

from dashboard_service import FileType

logging.basicConfig(level=logging.INFO)


class SampleOrchestrator:
    def __init__(self) -> None:
        """ "Load all gsa files to simulate a stream of data coming in"""
        self.message_stack = []
        with open("./short_list_of_data.txt") as f:
            for line in f:
                filepath = line.strip()
                with open(filepath, "rb") as file:
                    msg = FileType(
                        filename=os.path.basename(filepath),
                        file=base64.b64encode(file.read()),
                    )
                    # wait 5 seconds for each message
                    self.message_stack.append(
                        (
                            IntersectDirectMessageParams(
                                destination="nsdf-organization.nsdf-facility.nsdf-system.nsdf-subsystem.nsdf-dashboard-service",
                                operation="NSDFDashboard.get_bragg_data",
                                payload=msg,
                            ),
                            5.0,
                        )
                    )
        self.message_stack.reverse()

    def client_callback(
        self,
        _source: str,
        _operation: str,
        _has_error: bool,
        payload: INTERSECT_JSON_VALUE,
    ) -> IntersectClientCallback:
        if not self.message_stack:
            # break out of pub/sub loop
            raise Exception
        message, wait_time = self.message_stack.pop()
        time.sleep(wait_time)
        return IntersectClientCallback(messages_to_send=[message])


if __name__ == "__main__":
    from_config_file = {
        "brokers": [
            {
                "username": "intersect_username",
                "password": "intersect_password",
                "port": 1883,
                "protocol": "mqtt3.1.1",
            },
        ],
    }

    file_bytes = ""
    with open(f"./GSAS/NOM168361tof.gsa", "rb") as f:
        file_bytes = base64.b64encode(f.read())

    msg = FileType(filename="NOM168361tof.gsa", file=file_bytes)
    initial_messages = [
        IntersectDirectMessageParams(
            destination="nsdf-organization.nsdf-facility.nsdf-system.nsdf-subsystem.nsdf-dashboard-service",
            operation="NSDFDashboard.get_bragg_data",
            payload=msg,
        )
    ]

    config = IntersectClientConfig(
        initial_message_event_config=IntersectClientCallback(
            messages_to_send=initial_messages
        ),
        **from_config_file,
    )
    orchestrator = SampleOrchestrator()
    client = IntersectClient(
        config=config,
        user_callback=orchestrator.client_callback,
    )
    default_intersect_lifecycle_loop(
        client,
    )
