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
from constants import INTERSECT_DASHBOARD_CONFIG


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='nsdf-intersect-dashboard.log',
    encoding='utf-8',
    level=logging.INFO
)


class AppState:
    def __init__(self):
        # config
        self.config = {'volumes': {'bragg_volume': '', 'transition_volume': '', 'andie_volume': '','scientist_cloud_volume': ''}, 'scan_period': {
            'bragg_scan_period': 2, 'transition_scan_period': 2, 'select_scan_period': 45
        }}
        # data
        self.files = defaultdict()
        self.bragg_data = defaultdict()
        self.current_bragg_file = ""
        self.id_campaign = ""
        self.id_transition = ""
        self.id_andie = ""
        self.lastUpdate = datetime.now().strftime("%B %d, %Y %I:%M:%S %p UTC")
        self.next_temperature = 0.00
        self.next_temperature_timestamp = 0
        self.minX = 0.0
        self.minY = 0.0
        self.maxX = 0.0
        self.maxY = 0.0

        self.bragg_data_dict = dict(
            data=[],
            layout=go.Layout(
                title=dict(text="Bragg Data", font=dict(size=26, weight="bold")),
                xaxis=dict(title=dict(text="d-Spacing", font=dict(size=22)), tickfont=dict(size=18)),
                yaxis=dict(title=dict(text="Intensity", font=dict(size=22)), tickfont=dict(size=18)),
                legend=dict(font=dict(size=16))
            ),
        )
        self.transition_data_dict = dict(
            data=[
                go.Scatter(
                    mode="lines",
                    x=[],
                    y=[],
                    name="Next Temperature",
                    line=dict(width=3, color="green", dash="dash"),
                )
            ],
            layout=go.Layout(
                title=dict(text="Transition Plot", font=dict(size=26, weight="bold")),
                xaxis=dict(title=dict(text="Temperature (K)", font=dict(size=22)), tickfont=dict(size=18)),
                yaxis=dict(title=dict(text="d-Spacing", font=dict(size=22)), tickfont=dict(size=18)),
                legend=dict(font=dict(size=16))
            ),
        )
        self.stateful_plot_data_dict = dict(
            data=[],
            layout=go.Layout(
                title=dict(
                    text="Bragg Data Stateful Plot", font=dict(size=26, weight="bold")
                ),
                xaxis=dict(title=dict(text="d-Spacing", font=dict(size=22)), tickfont=dict(size=18)),
                yaxis=dict(title=dict(text="Intensity", font=dict(size=22)), tickfont=dict(size=18)),
                legend=dict(font=dict(size=16))
            ),
        )

        # plots/widgets
        self.bragg_data_plot = pn.pane.Plotly(
            self.bragg_data_dict,
            sizing_mode="stretch_both",
        )
        self.bragg_data_by_bank: List[pn.pane.Plotly] = []

        self.transition_plot = pn.pane.Plotly(
            self.transition_data_dict, sizing_mode="stretch_both"
        )

        self.stateful_plot = pn.pane.Plotly(
            self.stateful_plot_data_dict, sizing_mode="stretch_both"
        )

        self.by_bank_plot = pn.FlexBox(*self.bragg_data_by_bank)

        self.select_bragg_file = pn.widgets.AutocompleteInput(
            name="Bragg File Timestamp",
            restrict=True,
            options=self.files,
            case_sensitive=False,
            search_strategy="includes",
            placeholder="Select a Timestamp to Load",
            value="",
            min_characters=0,
        )

        self.xlim_slider = pn.widgets.FloatSlider(
            name="x-max",
            start=0.0,
            end=50.0,
            step=0.01,
            value=25.0,
        )
        self.ylim_slider = pn.widgets.FloatSlider(
            name="y-max", start=0.0, end=50.0, step=0.01, value=25.0
        )
        self.reset_axis_button = pn.widgets.Button(
            name="Reset Axes", button_type="success"
        )
        self.information_md = pn.pane.Markdown("""""")
        self.all_banks_header_md = pn.pane.Markdown("""""")
        self.andie_header_md = pn.pane.Markdown("""""")
        self.stateful_plot_header_md = pn.pane.Markdown("""""")

        self._render_information_content()

    def _load_stateful_files(self) -> DefaultDict[str, str]:
        """load files as timestamp/filename pair from the scientist cloud volume"""
        stateful_files = defaultdict()
        files = os.listdir(self.config['volumes']['scientist_cloud_volume'])
        if files:
            for file in files:
                if file.endswith(".gsa"):
                    epoch = int(file.split("_")[0])
                    human_readable_timestamp = datetime.fromtimestamp(
                        epoch, tz=timezone.utc
                    ).strftime("%B %d, %Y %I:%M:%S %p UTC")
                    stateful_files[human_readable_timestamp] = file

        return stateful_files

    def _load_workspace(self, filename: str):
        """load a gsas file into a workspace"""
        self.bragg_data = load_gsa_file(os.path.join(self.config['volumes']['bragg_volume'], filename))

    def _render_transition_content(self):
        """renders the transition plot using transition volume"""
        temp, ylist, traces = [], [], []
        maxX, maxY = self.next_temperature, 0.0
        with open(os.path.join(self.config['volumes']['transition_volume'], f"{self.id_campaign}_transition.txt")) as f:
            for line in f:
                data_tuple = line.strip().split(",")
                temp.append(float(data_tuple[1]))
                ylist.append([float(y) for y in data_tuple[2:]])
                maxX = max(maxX, temp[-1])
                maxY = max(maxY, max(ylist[-1]))

        # create traces
        N = len(ylist[0])
        for i in range(N):
            traces.append(
                go.Scatter(
                    mode="lines+markers",
                    x=temp,
                    y=[row[i] for row in ylist],
                    name=f"Peak {i+1}",
                    marker=dict(size=np.linspace(5, 35, len(temp))),
                    line=dict(width=1),
                )
            )
        # ANDiE trace
        traces.append(
            go.Scatter(
                mode="lines",
                x=[self.next_temperature, self.next_temperature],
                y=[0.0, maxY],
                name="Next Temperature",
                line=dict(width=3, color="green", dash="dash"),
            )
        )
        # patching transition plot
        self.transition_data_dict["data"] = traces
        self.transition_data_dict["layout"].xaxis.range = [130, max(maxX, self.next_temperature) + 20]
        self.transition_data_dict["layout"].title.text = f"Campaign: {self.id_campaign}"
        self.transition_plot.object = self.transition_data_dict

    def _render_andie_content(self):
        """renders the ANDiE prediction on the transition plot"""
        self.andie_header_md.object = f"""
            <div style="display: flex; gap: 16px;">
               <div style="border: 4px solid #00662c; padding: 8px; background-color: #e0f7e0; display: inline-block;
                    border-radius: 15px; font-size: 18px; font-family: Arial, sans-serif;">
                    🔴 <strong>Live:</strong> {datetime.fromtimestamp(self.next_temperature_timestamp, tz=timezone.utc).strftime("%B %d, %Y %I:%M:%S %p UTC")}
                </div>
                <div style="border: 4px solid #FBC02D; padding: 8px; background-color: #FFF9C4; display: inline-block;
                    border-radius: 15px; font-size: 18px; font-family: Arial, sans-serif;">
                    <strong>Next Temperature:</strong> {self.next_temperature} K
                </div>
            </div>
            """

        # update ANDiE trace in transition
        self.transition_data_dict["data"][-1].x = [
            self.next_temperature,
            self.next_temperature,
        ]
        maxX = self.transition_data_dict["layout"].xaxis.range[-1]
        if self.next_temperature > maxX:
            self.transition_data_dict["layout"].xaxis.range = [130, self.next_temperature + 20]
        # patching transition plot
        self.transition_plot.object = self.transition_data_dict

    def _render_information_content(self):
        """renders information content for the information tab"""
        self.information_md.object = f"""
        <style>
        .field {{
            font-size: 20px;
            font-weight: 400;
        }}

        .info-container {{
            border: 2px solid #00662c;
            border-radius: 15px;
            padding: 20px;
            background-color: #e0f7e0;
            width: 400px;
            margin: 10px;
        }}

        .title {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
            text-align: center;
            font-family: Arial, sans-serif;
            color: #333;
        }}
        </style>
        <div class="info-container">
            <div class="title">Dashboard Configuration</div>
            <div class="field">Bragg Plot Update Cycle: {self.config['scan_period']['bragg_scan_period']}s </div>
            <div class="field">Transition Plot Update Cycle: {self.config['scan_period']['transition_scan_period']}s </div>
            <div class="field">Stateful Plot Update Cycle: {self.config['scan_period']['select_scan_period']}s </div>
        </div>
        """

    def _render_bragg_plot(self):
        """renders a gsas workspace in the bragg plot and by bank tabs"""
        if self.current_bragg_file != "":
            ts = int(self.current_bragg_file.split("_")[0])
            self.lastUpdate = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%B %d, %Y %I:%M:%S %p UTC")
            # patching header
            self.all_banks_header_md.object = f"""
            <div style="border: 4px solid #00662c; padding: 8px; background-color: #e0f7e0; display: inline-block;
                border-radius: 15px; font-size: 18px; font-family: Arial, sans-serif;">
            🔴 <strong>Live:</strong> {self.lastUpdate}
            </div>
            """

            traces, self.maxX, self.maxY = [], 0.0, 0.0
            self.bragg_data_by_bank.clear()

            for wksp_index, arr in self.bragg_data.items():
                scatter_line = go.Scatter(
                    x=arr[0],
                    y=arr[1],
                    name=f"Bank {wksp_index}",
                    line=dict(width=2),
                )
                # setting plot limits
                self.minX = min(self.minX, np.min(arr[0]))
                self.maxX = max(self.maxX, np.max(arr[0]))
                self.minY = min(self.minX, np.min(arr[1]))
                self.maxY = max(self.maxY, np.max(arr[1]))

                # patching individual bank plot
                self.bragg_data_by_bank.append(
                    pn.pane.Plotly(dict(
                        data=scatter_line,
                        layout=go.Layout(
                            title=dict(text=f"Bank {wksp_index}", font=dict(size=26, weight="bold")),
                            xaxis=dict(title=dict(text="d-Spacing", font=dict(size=22)), tickfont=dict(size=18)),
                            yaxis=dict(title=dict(text="Intensity", font=dict(size=22)), tickfont=dict(size=18)),)
                    ), sizing_mode='stretch_width'))

                traces.append(scatter_line)

            self.by_bank_plot.objects = self.bragg_data_by_bank
            # setting slider limits
            self.xlim_slider.start = self.minX
            self.xlim_slider.end = self.xlim_slider.value = self.maxX
            self.ylim_slider.start = self.minY
            self.ylim_slider.end = self.ylim_slider.value = self.maxY
            # patching bragg data plot
            self.bragg_data_dict["data"] = traces
            self.bragg_data_dict["layout"].xaxis.range = [0, self.maxX]
            self.bragg_data_dict["layout"].yaxis.range = [0, 80]
            self.bragg_data_dict["layout"].title.text = self.current_bragg_file.split(".")[0]
            self.bragg_data_plot.object = self.bragg_data_dict

    def _render_bragg_content(self, name):
        """
        renders the bragg content by loading the workspace and rendering the plot
        """
        self._load_workspace(name)
        self._render_bragg_plot()

    def gen_figure_data(self, wksp_index: int, name: str):
        bank_data = dict(
            data=go.Scatter(
                x=self.wksp.dataX(wksp_index),
                y=self.wksp.dataY(wksp_index),
                name=name,
                line=dict(width=2),
            )
        )
        return bank_data

    def update_x_limit(self, lim: int):
        self.bragg_data_dict["layout"].xaxis.range = [0, lim]
        self.bragg_data_plot.object = self.bragg_data_dict

    def update_y_limit(self, lim: int):
        self.bragg_data_dict["layout"].yaxis.range = [0, lim]
        self.bragg_data_plot.object = self.bragg_data_dict

    def reset_limits(self, _):
        self.xlim_slider.value = self.maxX
        self.ylim_slider.value = self.maxY

    def update_stateful_plot(self, file):
        """updates the stateful plot when the select widget is triggered"""
        if file != "":
            traces = []
            bragg_data = load_gsa_file(os.path.join(self.config['volumes']['scientist_cloud_volume'], file))
            for wksp_index, data in bragg_data.items():
                name = file.split(".")[0]
                traces.append(
                    go.Scatter(
                        x=data[0],
                        y=data[1],
                        name=f"Bank {wksp_index}",
                        line=dict(width=2),
                    )
                )
            epoch = int(file.split("_")[0])
            human_readable_timestamp = datetime.fromtimestamp(
                epoch, tz=timezone.utc
            ).strftime("%B %d, %Y %I:%M:%S %p UTC")

            self.stateful_plot_header_md.object = f"""
            <div style="border: 4px solid #005b8c; padding: 8px; background-color: #e0f0f7; display: inline-block;
                border-radius: 15px; font-size: 18px; font-family: Arial, sans-serif;">
            <strong>Date:</strong> {human_readable_timestamp}
            </div>
            """

            self.stateful_plot_data_dict["data"] = traces
            self.stateful_plot_data_dict["layout"].yaxis.range = [0, 80]
            self.stateful_plot_data_dict["layout"].title.text = (
                f"Bragg Data: {file.split('.')[0]}"
            )
            self.stateful_plot.object = self.stateful_plot_data_dict

    def _last_id(self, plot: str, filename: str) -> str:
        """
        Returns the id of the last record of a given file.

        Args:
            plot(str): the plot that we want the last record (TRANSITION or ANDIE).
            filename(str): the name of the file to retrieve the record from.

        Returns:
            str: the id of the last record
        """

        match plot:
            case "TRANSITION":
                transition_state_path = os.path.join(self.config['volumes']['transition_volume'], filename)
                if not os.path.exists(transition_state_path):
                    return self.id_transition

                last_measure = ""
                with open(transition_state_path, 'r') as f:
                    for record in f:
                        last_measure = record

                return last_measure.strip().split(",")[0] if last_measure != "" else self.id_transition

            case "ANDIE":
                andie_state_path = os.path.join(self.config['volumes']['andie_volume'], "andie.txt")
                if not os.path.exists(andie_state_path):
                    return self.id_andie

                last_measure = ""
                with open(andie_state_path, 'r') as f:
                    for record in f:
                        last_measure = record

                if last_measure == "":
                    return self.id_andie

                last_measure = last_measure.strip().split(",")
                id, timestamp, next_temp = last_measure[1], int(last_measure[2]), float(last_measure[3])
                self.next_temperature_timestamp = timestamp
                self.next_temperature = next_temp
                return id

            case _:
                return ""

    # POLLING METHODS
    def poll_bragg(self):
        """
        Polling method to check, update, and render the bragg plot on an interval.
        """
        # Check volume and return if does not exist
        if not os.path.isdir(self.config['volumes']['bragg_volume']):
            logger.warning(f"Bragg volume: {self.config['volumes']['bragg_volume']} not found, skipping checks...")
            return

        files = os.listdir(self.config['volumes']['bragg_volume'])
        if files:
            files = sorted(files, key=lambda f: int(f.split("_")[0]))
            if files[-1] != self.current_bragg_file:
                self.current_bragg_file = files[-1]
                self._render_bragg_content(files[-1])

            if len(files) > 1:
                for i in range(len(files) - 1):
                    filepath = os.path.join(self.config['volumes']['bragg_volume'], files[i])
                    if os.path.exists(filepath):
                        os.remove(filepath)

    def poll_transition(self):
        """
        Polling method to check, update, and render the transition plot on an interval.
        """
        # Check volume and return if does not exist
        if not os.path.isdir(self.config['volumes']['transition_volume']):
            logger.warning(f"Transition volume: {self.config['volumes']['transition_volume']} not found, skipping checks...")
            return

        files = os.listdir(self.config['volumes']['transition_volume'])
        if files:
            if len(files) > 1:
                # change campaign id
                # NOTE: No support for parallel campaign (sequential only)
                prev_cid = self.id_campaign
                for file in files:
                    cid = file.split("_")[0]
                    if cid != self.id_campaign:
                        self.id_campaign = cid
                os.remove(os.path.join(self.config['volumes']['transition_volume'], f"{prev_cid}_transition.txt"))
            else:
                self.id_campaign = files[0].split("_")[0]

            id = self._last_id("TRANSITION", f"{self.id_campaign}_transition.txt")
            if id != self.id_transition:
                self.id_transition = id
                self._render_transition_content()

    def poll_andie(self):
        """
        Polling method to check, update, and render the ANDiE prediction on the transition plot on an interval.
        """
        # Check volume and return if does not exist
        if not os.path.isdir(self.config['volumes']['andie_volume']):
            logger.warning(f"ANDiE volume: {self.config['volumes']['andie_volume']} not found, skipping checks...")
            return

        id = self._last_id("ANDIE", "andie.txt")
        if id != self.id_andie:
            self.id_andie = id
            self._render_andie_content()

    def poll_transition_and_andie(self):
        """
        Synchronize polling of transition and ANDiE prediction on the same interval.
        """
        # update both to render ANDiE next temperature in transition
        self.poll_transition()
        self.poll_andie()

    def poll_stateful_files(self):
        """
        Polling method to check, update, and render the files available on the
        scientist cloud volume as options to a select widget on the controls on an interval.
        """
        # Check volume and return if does not exist
        if not os.path.isdir(self.config['volumes']['scientist_cloud_volume']):
            logger.warning(
                f"Scientist cloud volume: {self.config['volumes']['scientist_cloud_volume']} not found, "
                "skipping load stateful files..."
            )
            return

        self.files = self._load_stateful_files()
        self.select_bragg_file.options = self.files


def App() -> MaterialTemplate:
    pn.extension("plotly")
    app_state = AppState()

    config_path = os.getenv(INTERSECT_DASHBOARD_CONFIG, "/app/config_dashboard_default.yaml")
    try:
        with open(config_path) as f:
            app_state.config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"could not initialize dashboard, configuration path does not exists: {e}")
        raise FileNotFoundError(f"could to initialize dashboard, configuration path does not exists {e}")

    logger.info("initialized dashboard configuration")

    bragg_data_tab = pn.Column(
        pn.Row(app_state.all_banks_header_md),
        app_state.bragg_data_plot,
    )

    by_bank_tab = pn.Column(
        pn.pane.Markdown("<h1>By Bank</h1>"),
        app_state.by_bank_plot
    )

    transition_plot_tab = pn.Column(
        pn.Row(app_state.andie_header_md),
        app_state.transition_plot,
    )

    information_tab = pn.Row(app_state.information_md)

    stateful_plots_tab = pn.Column(
        app_state.stateful_plot_header_md, app_state.stateful_plot
    )

    main = pn.Tabs(
        ("Bragg Data", bragg_data_tab),
        ("By Bank", by_bank_tab),
        ("Transition Plot", transition_plot_tab),
        ("Timestamp", stateful_plots_tab),
        ("Information", information_tab),
        dynamic=True
    )

    sidebar = pn.Column(
        pn.pane.Markdown("<h1>Controls</h1>"),
        app_state.select_bragg_file,
        app_state.xlim_slider,
        app_state.ylim_slider,
        app_state.reset_axis_button,
    )

    # reactivity
    pn.bind(app_state.update_stateful_plot, app_state.select_bragg_file, watch=True)
    pn.bind(app_state.update_x_limit, app_state.xlim_slider, watch=True)
    pn.bind(app_state.update_y_limit, app_state.ylim_slider, watch=True)
    pn.bind(app_state.reset_limits, app_state.reset_axis_button, watch=True)

    template = pn.template.MaterialTemplate(
        title="NSDF INTERSECT",
        header=[],
        main=[main],
        sidebar=[sidebar],
        header_background="#00662c",
        busy_indicator=None,
        collapsed_sidebar=True
    )

    # Listen to changes in volumes in an interval which use polling methods
    pn.state.add_periodic_callback(
        callback=app_state.poll_bragg, period=app_state.config['scan_period']['bragg_scan_period'] * 1000
    )
    pn.state.add_periodic_callback(
        callback=app_state.poll_transition_and_andie,
        period=app_state.config['scan_period']['transition_scan_period'] * 1000,
    )

    pn.state.add_periodic_callback(
        callback=app_state.poll_stateful_files, period=app_state.config['scan_period']['select_scan_period']* 1000
    )
    return template


if __name__.startswith("bokeh"):
    try:
        app = App()
        app.servable()
    except Exception as e:
        logger.error(f"dashboard could not be initialized {e}")
