"""
File: dashboard.py
Author: NSDF-INTERSECT Team
License: BSD-3
Description: The UI/visualization component for monitoring experiments.
"""

import os
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



logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='nsdf-intersect-replay-dashboard.log',
    encoding='utf-8',
    level=logging.INFO
)


class BraggAppState:
    def __init__(self, config: dict):
        # config
        self.config = config
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
        """load files as timestamp/filename pair from the scientist cloud volume"""
        result_files = defaultdict()
        files = os.listdir(self.config['volumes']['scientist_cloud_volume'])
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
        file_path = os.path.join(self.config['volumes']['scientist_cloud_volume'], filename)
        if os.path.exists(file_path):
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
        else:
            logger.error(f"bragg file does not exist: {filename}")

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
    def __init__(self, config: dict):
        # config
        self.config = config
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
            value=0,
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

        self.render(force=True)

    def _load_files(self) -> DefaultDict[str, str]:
        """load files as campaign id list from the scientist cloud volume"""
        result_files = []
        files = os.listdir(self.config['volumes']['scientist_cloud_volume'])
        if files:
            for file in files:
                if file.endswith("_transition.txt"):
                    campaign_id = file.split("_")[0]
                    result_files.append(campaign_id)

        return result_files

    def load_file(self, campaign_id: str):
        """load a transition file"""
        filename = f"{campaign_id}_transition.txt"
        self.file_data = []
        self.point_options = []

        file_path = os.path.join(self.config['volumes']['scientist_cloud_volume'], filename)
        if os.path.exists(file_path):
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
            self.t = 0

            logger.info(f"loaded transition file: {filename}")
        elif campaign_id != "":
            logger.error(f"transition file does not exist: {filename}")

        self.render(force=True)

    def load_andie(self):
        """load the andie file for all transition files"""
        self.andie_data = defaultdict()

        file_path = os.path.join(self.config['volumes']['scientist_cloud_volume'], "andie.txt")
        if os.path.exists(file_path):
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
        else:
            logger.error(f"andie file does not exist.")

    def poll_files(self):
        """poll the scientist cloud volume for new transition files or updates to andie files"""
        self.files = self._load_files()
        self.select_file.options = self.files

        self.load_andie()

        # reactivity
        # pn.bind(self.update_stateful_plot, self.select_bragg_file, watch=True)

    def calculate_duration(self):
        if self.current_campaign_id is None:
            return 0, -1

        if self.current_campaign_id not in self.andie_data:
            return 0, -1

        andie_data = self.andie_data[self.current_campaign_id]

        if len(andie_data) <= 1:
            return 0, -1

        if len(andie_data) != len(self.file_data):
            return 0, -1
        
        start_t = float(andie_data[0][1])
        andie_end_t = float(andie_data[-1][1])
        last_delay = andie_end_t - float(andie_data[-2][1])
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
            traces.append(
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
            logger.error(f"campaign id {self.campaign_id} not found in andie data")
            return

        andie_data = self.andie_data[self.current_campaign_id]
        if len(andie_data) == 0:
            logger.error(f"andie data for campaign id {self.current_campaign_id} is empty")
            return

        if len(andie_data) != len(self.file_data):
            logger.error(f"andie data length {len(andie_data)} does not match transition data length {len(self.file_data)} for campaign id {self.current_campaign_id}")
            return

        duration, start_t = self.calculate_duration()
        andie_offset = start_t

        next_temperature = None
        andie_index = -1

        for i in range(len(andie_data)):
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
            self.play_pause_button.name = "⏸️"
            self.play_pause_button.button_type = "warning"
        else:
            self.play_pause_button.name = "▶️"
            self.play_pause_button.button_type = "success"

def App() -> MaterialTemplate:
    pn.extension("plotly")
    config = defaultdict()

    config_path = os.getenv("INTERSECT_REPLAY_DASHBOARD_CONFIG", "/config/config_dashboard_default.yaml")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"could not initialize replay dashboard, configuration path does not exists: {e}")
        raise FileNotFoundError(f"could to initialize replay dashboard, configuration path does not exists {e}")

    logger.info("initialized replay dashboard configuration")

    bragg_state = BraggAppState(config)
    transition_state = TransitionAppState(config)

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
        main=[main],
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

    return page


if __name__.startswith("bokeh"):
    try:
        app = App()
        app.servable()
    except Exception as e:
        logger.error(f"dashboard could not be initialized {e}")
