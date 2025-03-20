"""
File: realtime_client.py
Authors: NSDF-INTERSECT Team
License: BSD-3
Description: Test client for all the plots, simulating realtime.
"""

import base64
import logging
import time
import os
from uuid import uuid4
import yaml

from intersect_sdk import (
    INTERSECT_JSON_VALUE,
    IntersectClient,
    IntersectClientCallback,
    IntersectClientConfig,
    IntersectDirectMessageParams,
    default_intersect_lifecycle_loop,
)

from dashboard_service import FileType, NextTemperature, TransitionData

logging.basicConfig(level=logging.INFO)

# (temperature, peak 4.15, peak 4.6)
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


CONFIG_CLIENT = "config_client.yaml"


class SampleOrchestrator:
    def __init__(self) -> None:
        """ "Load all gsa files to simulate a stream of data coming in"""
        self.message_stack = []
        id_campaign = uuid4()
        for i in range(len(transition_data)):
            data = transition_data[i]
            nextpoint = (
                transition_data[i + 1][0]
                if i + 1 != len(transition_data)
                else transition_data[i][0]
            )

            # transition data
            self.message_stack.append(
                (
                    IntersectDirectMessageParams(
                        destination="nsdf.cloud.diffraction.dashboard.dashboard-service",
                        operation="NSDFDashboard.get_transition_data_single",
                        payload=TransitionData(
                            id=str(id_campaign),
                            temp=data[0],
                            ylist=data[1:],
                        ),
                    ),
                    2.0,
                )
            )
            # next temperature data
            self.message_stack.append(
                (
                    IntersectDirectMessageParams(
                        destination="nsdf.cloud.diffraction.dashboard.dashboard-service",
                        operation="NSDFDashboard.get_next_temperature",
                        payload=NextTemperature(
                            id=str(id_campaign),
                            data=nextpoint,
                            timestamp=int(time.time()),
                        ),
                    ),
                    2.0,
                )
            )

        # bragg data
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
                                destination="nsdf.cloud.diffraction.dashboard.dashboard-service",
                                operation="NSDFDashboard.get_bragg_data",
                                payload=msg,
                            ),
                            2.0,
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
    from_config_file = {}
    with open(CONFIG_CLIENT) as f:
        from_config_file = yaml.safe_load(f)

    orchestrator = SampleOrchestrator()
    config = IntersectClientConfig(
        initial_message_event_config=IntersectClientCallback(
            messages_to_send=[orchestrator.message_stack.pop()[0]]
        ),
        **from_config_file,
    )
    client = IntersectClient(
        config=config,
        user_callback=orchestrator.client_callback,
    )
    default_intersect_lifecycle_loop(
        client,
    )
