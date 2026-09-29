"""
File: dashboard.py
Author: NSDF-INTERSECT Team
License: BSD-3
Description: The UI/visualization component for monitoring experiments.
"""

import os
import shutil
import logging
from typing import List, DefaultDict
from collections import defaultdict
import panel as pn
from panel.template import MaterialTemplate
import plotly.graph_objects as go
from datetime import datetime, timezone
import numpy as np
import yaml
from gsa_loader import load_gsa_file
import boto3
from dotenv import load_dotenv
from botocore.client import Config
from concurrent import futures
from concurrent.futures import ProcessPoolExecutor
import uuid
import hashlib

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='nsdf-intersect-replay-dashboard.log',
    encoding='utf-8',
    level=logging.INFO
)

class FileProvider:
    def __init__(self, config, resource):
        self.config = config
        self.s3 = resource
        self.bucket = resource.Bucket(config["scientist_cloud"]["bucket"])
        self.output_folder = config['volumes']['scientist_cloud_volume']
        self.path_prefix = self.config["scientist_cloud"]["path"]
        self.downloaded_files = []

        os.makedirs(self.output_folder, exist_ok=True)

        if self.path_prefix[-1] != "/":
            self.path_prefix += "/"

        self.modal = pn.Modal(pn.pane.Markdown("<h1>Loading data...</h1>"),
                name = "Loading Files",
                show_close_button = False,
                background_close = False,
                open = False)
    
    def poll_bragg_files(self):
        file_summaries = self.bucket.objects.filter(Prefix = self.path_prefix + "bragg/")
        return [summary.key.split("/")[-1] for summary in file_summaries]

    def poll_transition_files(self):
        file_summaries = self.bucket.objects.filter(Prefix = self.path_prefix + "transition/")
        return [summary.key.split("/")[-1] for summary in file_summaries]

    def load_andie_file(self) -> str:
        output_path = os.path.join(self.output_folder, "andie.txt")
        
        if os.path.exists(output_path):
            return output_path

        self.bucket.download_file(self.path_prefix + "nexttemp/" + self.config["scientist_cloud"]["andie_name"], output_path)
        self.downloaded_files.append(output_path)

        return output_path

    def load_bragg_file(self, file_name: str) -> str:
        output_path = os.path.join(self.output_folder, file_name)

        if os.path.exists(output_path):
            return output_path

        self.modal.show()

        self.bucket.download_file(self.path_prefix + "bragg/" + file_name, output_path)
        self.downloaded_files.append(output_path)

        self.modal.hide()

        return output_path

    def load_transition_file(self, file_name: str) -> str:
        output_path = os.path.join(self.output_folder, file_name)

        if os.path.exists(output_path):
            return output_path

        self.modal.show()

        self.bucket.download_file(self.path_prefix + "transition/" + file_name, output_path)
        self.downloaded_files.append(output_path)

        self.modal.hide()

        return output_path

class BraggAppState:
    def __init__(self, config: dict, file_provider: FileProvider):
        self.config = config
        self.file_provider = file_provider
        self.files = defaultdict()
        self.bank_options = defaultdict()

        # data
        self.data_dict = dict(
            data=[],
            layout=go.Layout(
                xaxis=dict(title=dict(text="d-Spacing", font=dict(size=22)), tickfont=dict(size=18)),
                yaxis=dict(title=dict(text="Intensity", font=dict(size=22)), tickfont=dict(size=18)),
                legend=dict(font=dict(size=16))
            ),
        )

        # plots/widgets
        self.data_plot = pn.pane.Plotly(
            self.data_dict,
            sizing_mode="stretch_both",
            styles={"margin_top": "-30px", "z-index": "-1"}
        )
        self.bragg_data_by_bank: dict = []

        self.select_file = pn.widgets.AutocompleteInput(
            name="Bragg File Timestamp",
            restrict=True,
            options=self.files,
            case_sensitive=False,
            search_strategy="includes",
            placeholder="Select a Timestamp to Load",
            value="",
            min_characters=0,
        )

        self.select_bank = pn.widgets.AutocompleteInput(
            name="Bragg Bank",
            restrict=True,
            options=self.bank_options,
            case_sensitive=False,
            search_strategy="includes",
            placeholder="Select a Bragg Bank to View",
            value=0,
            min_characters=0
        )

        self.poll_files()

    def _load_files(self) -> DefaultDict[str, str]:
        """load files as timestamp/filename pair from the scientist cloud"""
        result_files = defaultdict()
        files = self.file_provider.poll_bragg_files()
        if files:
            for file in files:
                if file.endswith(".gsa"):
                    epoch = int(file.split("_")[0])
                    human_readable_timestamp = datetime.fromtimestamp(
                        epoch, tz=timezone.utc
                    ).strftime("%B %d, %Y %I:%M:%S %p UTC")
                    result_files[human_readable_timestamp] = file

        return result_files

    def load_file(self, filename: str):
        """load a bragg file and update the plot"""
        file_path = self.file_provider.load_bragg_file(filename)

        self.bragg_data_by_bank = defaultdict()
        self.bank_options = defaultdict()

        for bank_id, arr in load_gsa_file(file_path).items():
            self.bank_options["Bank " + str(bank_id)] = bank_id
            self.bragg_data_by_bank[bank_id] = go.Scatter(
                x=arr[0],
                y=arr[1],
                name=f"Bank {bank_id}",
                line=dict(width=2),
            )

        self.bank_options["All Banks"] = -1
        self.select_bank.options = self.bank_options
        self.select_bank.value = -1

        self.display_plot(-1)

        logger.info(f"loaded bragg file: {filename}")

    def display_plot(self, bank_id: int):
        if type(bank_id) != int:
            return

        """display the bragg plot for the selected bank"""
        if bank_id == -1:
            self.data_dict["data"] = list(self.bragg_data_by_bank.values())
        else:
            self.data_dict["data"] = [self.bragg_data_by_bank[bank_id]]

        self.data_plot.object = self.data_dict

    def poll_files(self):
        """poll the scientist cloud volume for new bragg files"""
        self.files = self._load_files()
        self.select_file.options = self.files

class TransitionAppState:
    def __init__(self, config: dict, file_provider: FileProvider):
        self.config = config
        self.file_provider = file_provider
        self.files = []
        self.point_options = []
        self.file_data = defaultdict()
        self.andie_data = defaultdict()
        self.playing = False

        self._program_changed_value = False

        self.current_campaign_id = None
        self.t = 0.0

        self.last_andie_index = -1
        self.last_transition_index = -1

        # data
        self.data_dict = dict(
            data=[],
            layout=go.Layout(
                xaxis=dict(title=dict(text="Temperature (K)", font=dict(size=22)), tickfont=dict(size=18)),
                yaxis=dict(title=dict(text="d-Spacing", font=dict(size=22)), tickfont=dict(size=18)),
                legend=dict(font=dict(size=16))
            ),
        )

        self.select_file = pn.widgets.AutocompleteInput(
            name="Campaign ID",
            restrict=True,
            options=self.files,
            case_sensitive=False,
            search_strategy="includes",
            placeholder="Select a Campaign ID to View",
            value="",
            min_characters=0
        )

        # plots/widgets
        self.data_plot = pn.pane.Plotly(
            self.data_dict,
            sizing_mode="stretch_both",
            styles={"margin_top": "-30px", "z-index": "-1"}
        )

        self.time_slider = pn.widgets.FloatSlider(
            name="Time", start=0.0, end=0.1, step=1, value=0.0
        )
        self.time_scale_slider = pn.widgets.FloatSlider(
            name="Time Scale", start=1.0, end=1000.0, step=1, value=500.0, width=100
        )
        self.play_pause_button = pn.widgets.Button(
            name="▶️", button_type="success"
        )

        self.select_point = pn.widgets.AutocompleteInput(
            name="Point ID",
            restrict=True,
            options=self.point_options,
            case_sensitive=False,
            search_strategy="includes",
            placeholder="Select a Point ID to Jump to",
            value="",
            min_characters=0,
        )

        self.next_temperature_md = pn.pane.Markdown("<h2>Next Temperature: --</h2>")

        self.load_andie()
        self.poll_files()
        self.render(force=True)

    def _load_files(self) -> DefaultDict[str, str]:
        """load files as campaign id list from the scientist cloud volume"""
        result_files = []
        files = self.file_provider.poll_transition_files()
        if files:
            for file in files:
                if file.endswith("_transition.txt"):
                    campaign_id = file.split("_")[0]

                    if campaign_id in self.andie_data:
                        result_files.append(campaign_id)

        result_files.sort(key=lambda file: self.andie_data[file][0][1])

        return [result_files[i]+" (Campaign " + str(i + 1) + ")" for i in range(len(result_files))]

    def load_file(self, selection_name: str):
        """load a transition file"""

        if selection_name == "":
            self.render(force=True)
            return

        self.pause()

        campaign_id = selection_name.split(" ")[0]

        filename = f"{campaign_id}_transition.txt"
        self.file_data = []
        self.point_options = []

        file_path = self.file_provider.load_transition_file(filename)
        
        self.bragg_data_by_bank = defaultdict()
        self.bank_options = defaultdict()
        self.current_campaign_id = campaign_id

        with open(file_path, "r") as file:
            for line in file:
                parts = line.strip().split(",") # point_id, temperature, d-spacings...
                point_id = parts[0]
                self.file_data.append(parts) 
                self.point_options.append(point_id)

        self.select_point.options = self.point_options
        duration, _ = self.calculate_duration()
        self.t = duration
        self.update_time_slider()

        logger.info(f"loaded transition file: {filename}")

        self.render(force=True)

    def load_andie(self):
        """load the andie file for all transition files"""
        self.andie_data = defaultdict()

        file_path = self.file_provider.load_andie_file()

        with open(file_path, "r") as file:
            for line in file:
                parts = line.strip().split(",")
                campaign_id = parts[0]
                if not (campaign_id in self.andie_data):
                    self.andie_data[campaign_id] = []

                self.andie_data[campaign_id].append([parts[1], parts[2], parts[3]]) # reading_id, timestamp, temperature

        for points in self.andie_data.values():
            points.sort(key=lambda entry: entry[1]) # sort by timestamp

        self.render()

    def poll_files(self):
        """poll the scientist cloud volume for new transition files or updates to andie files"""
        self.files = self._load_files()
        self.select_file.options = self.files

        # reactivity
        # pn.bind(self.update_stateful_plot, self.select_bragg_file, watch=True)

    def calculate_duration(self):
        if self.current_campaign_id is None:
            return 0, -1

        if self.current_campaign_id not in self.andie_data:
            return 0, -1

        andie_data = self.andie_data[self.current_campaign_id]

        if len(andie_data) == 0:
            return 0, -1

        if len(andie_data) < len(self.file_data):
            return 0, -1

        if len(self.file_data) == 1:
            return 0, float(andie_data[0][1])

        file_len = len(self.file_data)
        start_t = float(andie_data[0][1])
        andie_end_t = float(andie_data[file_len-1][1])
        last_delay = andie_end_t - float(andie_data[file_len-2][1])
        end_t = andie_end_t + last_delay

        return end_t - start_t, start_t

    def generate_transition_plot(self, max_transition_index: int, next_temperature: float):
        max_transition_index = min(max_transition_index, len(self.file_data) - 1)

        traces = []
        max_y = 0.0

        x_list = [] # list of temperatures


        if max_transition_index >= 0:
            for i in range(max_transition_index + 1):
                x_list.append(float(self.file_data[i][1]))

            num_peaks = len(self.file_data[0]) - 2
            for peak in range(num_peaks):
                
                y_list = [] # list of d-spacings for this peak

                for i in range(max_transition_index + 1):
                    y_val = float(self.file_data[i][2 + peak])
                    y_list.append(y_val)
                    max_y = max(max_y, y_val)

                traces.append(
                    go.Scatter(
                        mode="lines+markers",
                        x=x_list,
                        y=y_list, 
                        name=f"Peak {peak+1}",
                        marker=dict(size=np.linspace(5, 35, len(self.file_data))),
                        line=dict(width=1),
                    )
                )

        if next_temperature is not None:
            traces.insert(
                0,
                go.Scatter(
                    mode="lines",
                    x=[next_temperature, next_temperature],
                    y=[0.0, max(max_y * 1.1, 1.0)],
                    name="Next Temperature",
                    line=dict(width=3, color="green", dash="dash"),
                )
            )

        return traces

    def update_time_slider(self):
        duration, _ = self.calculate_duration()
        self.time_slider.start = 0.0
        self.time_slider.end = max(duration, 0.1)
        self.t = min(self.t, duration)
        self._program_changed_value = True
        self.time_slider.value = self.t
        self._program_changed_value = False

    def render(self, force: bool = False):
        self.update_time_slider()

        if self.current_campaign_id is None:
            return

        if self.current_campaign_id not in self.andie_data:
            logger.error(f"campaign id {self.current_campaign_id} not found in andie data")
            return

        andie_data = self.andie_data[self.current_campaign_id]
        if len(andie_data) == 0:
            logger.error(f"andie data for campaign id {self.current_campaign_id} is empty")
            return

        if len(andie_data) < len(self.file_data):
            logger.error(f"andie data length {len(andie_data)} is shorter than transition data length {len(self.file_data)} for campaign id {self.current_campaign_id}")
            return

        duration, start_t = self.calculate_duration()
        andie_offset = start_t

        next_temperature = None
        andie_index = -1

        for i in range(len(self.file_data)):
            entry = andie_data[i]
            if float(entry[1]) <= self.t + andie_offset:
                next_temperature = float(entry[2])
                andie_index = i
            else:
                break

        transition_index = andie_index - 1
        if duration - self.t < 0.001:
            transition_index = len(self.file_data) - 1

        if transition_index < 0:
            transition_index = -1

        if self.last_andie_index == andie_index and self.last_transition_index == transition_index and not force:
            return

        self.last_andie_index = andie_index
        self.last_transition_index = transition_index

        self.data_dict["data"] = self.generate_transition_plot(transition_index, next_temperature)
        self.data_plot.object = self.data_dict

        if transition_index >= 0:
            self._program_changed_value = True
            self.select_point.value = self.file_data[transition_index][0]
            self._program_changed_value = False
        else:
            self._program_changed_value = True
            self.select_point.value = ""
            self._program_changed_value = False

        if next_temperature is not None:
            self.next_temperature_md.object = f"<h2>Next Temperature: {next_temperature}</h2>"
        else:
            self.next_temperature_md.object = f"<h2>Next Temperature: --</h2>"

    def jump_to_point(self, point_id: str):
        if self._program_changed_value:
            self._program_changed_value = False
            return
        
        if point_id == "":
            return

        if self.current_campaign_id is None:
            return

        if self.current_campaign_id not in self.andie_data:
            return

        transition_index = -1
        for i in range(len(self.file_data)):
            if self.file_data[i][0] == point_id:
                transition_index = i
                break

        if transition_index == -1:
            logger.error(f"point id {point_id} not found in transition data")
            return

        andie_data = self.andie_data[self.current_campaign_id]

        self.pause()
        duration, start_t = self.calculate_duration()

        andie_index = transition_index + 1
        if andie_index >= len(andie_data):
            self.set_t(duration)
            return

        andie_entry = andie_data[andie_index]
        timestamp = float(andie_entry[1])
        self.set_t(timestamp - start_t)

    def set_t(self, t: float):
        if self._program_changed_value:
            self._program_changed_value = False
            return

        if t == self.t:
            return

        self.t = t
        self.render()

    def step_time(self, real_delta_time: float):
        if not self.playing:
            return

        time_scale = self.time_scale_slider.value
        delta_t = real_delta_time * time_scale
        new_t = self.t + delta_t

        duration, _ = self.calculate_duration()
        if new_t > duration:
            self.pause()
            new_t = duration

        self.set_t(new_t)

    def play(self):
        if not self.playing:
            self.toggle_play_pause()

    def pause(self):
            if self.playing:
                self.toggle_play_pause()

    def toggle_play_pause(self):
        self.playing = not self.playing
        if self.playing:
            duration, _ = self.calculate_duration()
            
            if (duration - self.t < 0.01):
                self.t = 0
                self.update_time_slider()

            self.play_pause_button.name = "⏸️"
            self.play_pause_button.button_type = "warning"
        else:
            self.play_pause_button.name = "▶️"
            self.play_pause_button.button_type = "success"

def App() -> MaterialTemplate:
    pn.extension("plotly")
    pn.extension("modal")
    config = defaultdict()
    load_dotenv()

    config_path = os.getenv("INTERSECT_REPLAY_DASHBOARD_CONFIG", "/app/config/config_dashboard_default.yaml")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"could not initialize replay dashboard, configuration path does not exists: {e}")
        raise FileNotFoundError(f"could to initialize replay dashboard, configuration path does not exists: {e}")

    logger.info("initialized replay dashboard configuration")

    session = boto3.Session(aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID"),
                                    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
                                    region_name=os.getenv("AWS_REGION_NAME"))
    s3 = session.resource("s3",
                                endpoint_url='https://us-east-1.gw.future-tech-holdings.com',
                                config=Config(signature_version="s3v4"))

    file_provider = FileProvider(config, s3)

    bragg_state = BraggAppState(config, file_provider)
    transition_state = TransitionAppState(config, file_provider)

    transition_time_controls = pn.Row(
        transition_state.time_scale_slider,
        transition_state.play_pause_button,
        transition_state.time_slider
    )

    transition_bottom_bar = pn.Column(
        pn.Row(
            transition_time_controls,
            styles = {"width": "100%", "justify-content": "center"}
        ),
        stylesheets=["""
            :host {
                position: fixed;
                bottom: 0;
                right: 0;
                background-color: #ffffff;
                box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
                padding: 10px;
                z-index: 1000;
            }
        """],
        #styles={"width": "100%"}
    )

    bragg_data = pn.Column(
        pn.pane.Markdown("<h1>Bragg Data</h1>"),
        bragg_state.select_file,
        bragg_state.select_bank,
        bragg_state.data_plot
    )
    
    transition_data = pn.Column(
        pn.pane.Markdown("<h1>Transition Data</h1>"),
        pn.Row(transition_state.select_file, transition_state.select_point),
        transition_state.next_temperature_md,
        transition_state.data_plot,
        transition_bottom_bar
    )

    main = pn.Row(
        bragg_data,
        transition_data,
        styles={"padding_bottom": "100px"}
    )

    page = pn.template.MaterialTemplate(
        title="NSDF INTERSECT REPLAY",
        header=[],
        main=[pn.Column(main, file_provider.modal)],
        sidebar=[],
        header_background="#00662c",
        busy_indicator=None
    )

    # Listen to changes in volumes in an interval which use polling methods
    # pn.state.add_periodic_callback(
    #     callback=app_state.poll_bragg, period=app_state.config['scan_period']['bragg_scan_period'] * 1000
    # )

    pn.state.add_periodic_callback(
        callback=bragg_state.poll_files, period=config['delays']['file_polling_delay'] * 1000
    )
    pn.state.add_periodic_callback(
        callback=transition_state.poll_files, period=config['delays']['file_polling_delay'] * 1000
    )

    frame_delay = config['delays']['time_update_delay']
    pn.state.add_periodic_callback(
        callback=lambda: transition_state.step_time(frame_delay), period=int(frame_delay * 1000)
    )

    # reactivity
    pn.bind(bragg_state.load_file, bragg_state.select_file, watch=True)
    pn.bind(bragg_state.display_plot, bragg_state.select_bank, watch=True)

    pn.bind(transition_state.load_file, transition_state.select_file, watch=True)
    pn.bind(transition_state.set_t, transition_state.time_slider, watch=True)
    pn.bind(transition_state.jump_to_point, transition_state.select_point, watch=True)
    pn.bind(lambda _: transition_state.toggle_play_pause(), transition_state.play_pause_button, watch=True)

    page.servable()

    return page


if __name__.startswith("bokeh"):
    # try:
        app = App()
    # except Exception as e:
    #     logger.error(f"dashboard could not be initialized {e}")
