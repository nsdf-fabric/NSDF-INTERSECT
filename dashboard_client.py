import base64
import logging
import yaml

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

CONFIG_CLIENT = "config_client.yaml"


def simple_client_callback(
    _source: str, _operation: str, _has_error: bool, payload: INTERSECT_JSON_VALUE
) -> None:
    # raise exception to break out of message loop - we only send and wait for one message
    print(payload)
    raise Exception


if __name__ == "__main__":
    from_config_file = {}
    with open(CONFIG_CLIENT) as f:
        from_config_file = yaml.safe_load(f)

    file_bytes = ""
    with open("./GSAS/NOM168361tof.gsa", "rb") as f:
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

    client = IntersectClient(
        config=config,
        user_callback=simple_client_callback,
    )

    default_intersect_lifecycle_loop(
        client,
    )
