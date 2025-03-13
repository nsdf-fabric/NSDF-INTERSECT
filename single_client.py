"""
File: single_client.py
Authors: NSDF-INTERSECT Team
License: BSD-3
Description: Test client for single file.
Granular control over endpoint hit (bragg, transition, next_temperature)
"""

import base64
import time
import logging
import os
from uuid import uuid4
import yaml
import argparse

from intersect_sdk import (
    INTERSECT_JSON_VALUE,
    IntersectClient,
    IntersectClientCallback,
    IntersectClientConfig,
    IntersectDirectMessageParams,
    default_intersect_lifecycle_loop,
)

from dashboard_service import FileType, TransitionData, NextTemperature

logging.basicConfig(level=logging.INFO)
CONFIG_CLIENT = "config_client.yaml"

transition_data = [
    [284.89, 0.9353496748096445, 1.5583828040832086],
    [254.35, 0.9593545802124851, 1.518297300537268],
    [223.70, 1.3823875864760664, 0.4874543764356896],
    [193.12, 1.4157802771688555, 0.1756217650181439],
    [162.52, 1.4390218632340372, 0.16627265828482923],
    [133.62, 1.4543205011571554, 0.1635803842729867],
    [109.65, 1.4728294267657296, 0.16461256521244444],
    [114.22, 1.4966516476803589, 0.17084290781465622],
    [144.87, 1.4596272382692497, 0.1653306467096712],
    [175.33, 1.4403110733676547, 0.1673501661199693],
    [205.83, 1.4162563616488388, 0.17617271951369262],
    [236.28, 1.4501907494856883, 0.24460016281717184],
    [266.73, 1.0933614117922954, 1.580483590531685],
    [297.24, 1.000631281195945, 1.6620921253251981],
    [327.73, 0.9798321872710772, 1.6438979933610969],
    [358.19, 0.9816214248711559, 1.6508995326520444],
    [388.63, 1.0441782528831087, 1.7788399824092802],
    [419.13, 0.9917787260268168, 1.6779053042973953],
    [449.63, 0.938870612286109, 1.583080969633192],
    [480.08, 0.8538645527724241, 1.4390464484806835],
    [499.58, 0.832638773727295, 1.3975271870810835],
    [485.08, 0.8304213180571068, 1.390285256837193],
    [454.57, 0.842821810851089, 1.4187568866783322],
    [424.06, 0.8650983660430783, 1.4581591866105152],
    [393.61, 0.8824391533502394, 1.4825802390420455],
    [363.11, 0.89852383187218, 1.5096140144902985],
    [332.66, 0.9146561886436411, 1.5320231860195144],
    [302.21, 0.9279636564850444, 1.5513847817615285],
    [271.72, 0.9442621912819278, 1.5623201019075943],
    [241.27, 1.094419748916708, 1.2300321281899966],
    [211.28, 1.384045747896104, 0.2010486085851101],
    [199.83, 1.4254984254522678, 0.17142383895130625],
    [200.00, 1.426667976082179, 0.16991445836095545],
]


def prepare_bragg_messages(n: int = 1):
    messages = []
    files = os.listdir("GSAS")
    for i in range(min(n, len(files))):
        file_bytes = ""
        with open(f"./GSAS/{files[i]}", "rb") as f:
            file_bytes = base64.b64encode(f.read())
        msg = FileType(filename=files[i], file=file_bytes)
        messages.append(
            IntersectDirectMessageParams(
                destination="nsdf-organization.nsdf-facility.nsdf-system.nsdf-subsystem.nsdf-dashboard-service",
                operation="NSDFDashboard.get_bragg_data",
                payload=msg,
            )
        )
    return messages


def prepare_transition_message():
    return IntersectDirectMessageParams(
        destination="nsdf-organization.nsdf-facility.nsdf-system.nsdf-subsystem.nsdf-dashboard-service",
        operation="NSDFDashboard.get_transition_data",
        payload=TransitionData(
            id=str(uuid4()), temp=transition_data[0][0], ylist=transition_data[0][1:]
        ),
    )


def prepare_next_temperature_message(val=225.0):
    return IntersectDirectMessageParams(
        destination="nsdf-organization.nsdf-facility.nsdf-system.nsdf-subsystem.nsdf-dashboard-service",
        operation="NSDFDashboard.get_next_temperature",
        payload=NextTemperature(id=str(uuid4()), data=val, timestamp=int(time.time())),
    )


def simple_client_callback(
    _source: str, _operation: str, _has_error: bool, payload: INTERSECT_JSON_VALUE
) -> None:
    # raise exception to break out of message loop - we only send and wait for one message
    print(payload)
    raise Exception


def main():
    from_config_file = {}
    with open(CONFIG_CLIENT) as f:
        from_config_file = yaml.safe_load(f)

    parser = argparse.ArgumentParser(description="Dashboard single file client")
    parser.add_argument(
        "--bragg", action="store_true", default=False, help="send bragg file"
    )
    parser.add_argument(
        "--tpoint", action="store_true", default=False, help="send transition data"
    )
    parser.add_argument(
        "--next-temp",
        action="store_true",
        default=False,
        help="send next temperature data",
    )
    parser.add_argument("--n", default=1, help="number of bragg files to send")
    parser.add_argument("--val", default=225.0, help="next temperature custom value")
    args = parser.parse_args()

    initial_messages = []
    if args.bragg:
        for msg in prepare_bragg_messages(args.n):
            initial_messages.append(msg)
    if args.tpoint:
        initial_messages.append(prepare_transition_message())
    if args.next_temp:
        initial_messages.append(prepare_next_temperature_message(args.val))

    if len(initial_messages) == 0:
        return

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


if __name__ == "__main__":
    main()
