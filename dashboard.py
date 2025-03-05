import os
from typing import List, DefaultDict
from collections import defaultdict
import panel as pn
from load_gsas import load_gsas
import plotly.graph_objects as go
from datetime import datetime, timezone
import numpy as np

MAX_BANKS = 6
BRAGG_DIR = "./bragg_data"
TRANSITION_DATA_DIR = "./transition_data"
NEXT_TEMPERATURE_DIR = "./next_temperature_data"
STATEFUL_DATA_DIR = "./scientist_cloud_volume"
DELAY = 2


class AppState:
    def __init__(self):
        # data
        self.files = self.load_stateful_files()
        self.current_bragg_file = ""
        self.current_transition_file = ""
        self.current_next_temperature_file = ""
        self.wksp = None
        self.wksp_title = ""
        self.name = "No file"
        self.nEvents = 0
        self.lastUpdate = datetime.now().strftime("%A, %B %d, %Y %I:%M:%S %p UTC")
        self.next_temperature = 0.00
        self.minX = 0.0
        self.minY = 0.0
        self.maxX = 0.0
        self.maxY = 0.0
        self.bragg_data_dict = dict(
            data=[],
            layout=go.Layout(
                title=dict(text="Bragg Data", font=dict(size=22, weight="bold")),
                xaxis=dict(title="d-Spacing"),
                yaxis=dict(title="Intensity"),
            ),
        )
        self.bragg_data_by_bank_dict = [
            dict(
                data=[],
                layout=go.Layout(
                    title=dict(text=f"Bank {i+1}", font=dict(size=22, weight="bold")),
                    xaxis=dict(title="d-Spacing"),
                    yaxis=dict(title="Intensity"),
                ),
            )
            for i in range(MAX_BANKS)
        ]
        self.transition_data_dict = dict(
            data=[],
            layout=go.Layout(
                title=dict(text="Transition Plot", font=dict(size=22, weight="bold")),
                xaxis=dict(title="Temperature (K)"),
                yaxis=dict(title="d-Spacing"),
            ),
        )
        self.stateful_plot_data_dict = dict(
            data=[],
            layout=go.Layout(
                title=dict(
                    text="Bragg Data Stateful Plot", font=dict(size=22, weight="bold")
                ),
                xaxis=dict(title="d-Spacing"),
                yaxis=dict(title="Intensity"),
            ),
        )

        # plots/widgets
        self.bragg_data_plot = pn.pane.Plotly(
            self.bragg_data_dict,
            sizing_mode="stretch_both",
        )
        self.bragg_data_by_bank_plots: List[pn.pane.Plotly] = [
            pn.pane.Plotly(self.bragg_data_by_bank_dict[i]) for i in range(MAX_BANKS)
        ]
        self.transition_plot = pn.pane.Plotly(
            self.transition_data_dict, sizing_mode="stretch_both"
        )

        self.stateful_plot = pn.pane.Plotly(
            self.stateful_plot_data_dict, sizing_mode="stretch_both"
        )

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
        self.wkspinfo_md = pn.pane.Markdown("""""")
        self.all_banks_header_md = pn.pane.Markdown("""""")
        self.andie_header_md = pn.pane.Markdown("""""")
        self.stateful_plot_header_md = pn.pane.Markdown("""""")

        self.render_sidebar_content()
        self.render_main_content()

    def load_stateful_files(self) -> DefaultDict[str, str]:
        files = os.listdir(STATEFUL_DATA_DIR)
        stateful_files = defaultdict()
        if files:
            for file in files:
                if file.endswith(".gsa"):
                    epoch = int(file.split("_")[0])
                    human_readable_timestamp = datetime.fromtimestamp(
                        epoch, tz=timezone.utc
                    ).strftime("%A, %B %d, %Y %I:%M:%S %p UTC")
                    stateful_files[human_readable_timestamp] = file

        return stateful_files

    def load_workspace(self, filename: str):
        self.wksp = load_gsas(os.path.join(BRAGG_DIR, filename))
        self.name = self.wksp.name()
        self.wksp_title = self.wksp.getTitle()
        self.nEvents = self.wksp.getNEvents()

    def render_transition_content(self, filename):
        temp, peak1, peak2 = [], [], []
        traces = []

        with open(os.path.join(TRANSITION_DATA_DIR, filename)) as f:
            for line in f:
                data_tuple = line.strip().split(",")
                temp.append(float(data_tuple[0]))
                peak1.append(float(data_tuple[1]))
                peak2.append(float(data_tuple[2]))

        # peak 1
        traces.append(
            go.Scatter(
                mode="lines+markers",
                x=temp,
                y=peak1,
                name="peak X = 4.15",
                marker=dict(size=np.linspace(5, 35, len(temp))),
                line=dict(width=1),
            )
        )
        # peak 2
        traces.append(
            go.Scatter(
                mode="lines+markers",
                x=temp,
                y=peak2,
                name="peak X = 4.6",
                marker=dict(size=np.linspace(5, 35, len(temp))),
                line=dict(width=1),
            )
        )
        # patching transition plot
        self.transition_data_dict["data"] = traces
        self.transition_plot.object = self.transition_data_dict

    def render_sidebar_content(self):
        self.wkspinfo_md.object = f"""
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
            <div class="title">Workspace Information</div>
            <div class="field">Filename: {self.name} </div>
            <div class="field">Number of Events: {self.nEvents}</div>
        </div>
        <div class="info-container">
            <div class="title">Dashboard configuration</div>
            <div class="field">Cycle update: {DELAY}s </div>
        </div>
        """

    def render_main_content(self):
        if self.wksp:
            self.lastUpdate = datetime.now().strftime("%A, %B %d, %Y %I:%M:%S %p UTC")
            # patching header
            self.all_banks_header_md.object = f"""
            <div style="border: 4px solid #00662c; padding: 8px; background-color: #e0f7e0; display: inline-block; 
                border-radius: 15px; font-size: 18px; font-family: Arial, sans-serif;">
            🔴 <strong>Live:</strong> {self.lastUpdate}
            </div>
            """

            traces, self.maxX, self.maxY = [], 0.0, 0.0

            for bank_number in self.wksp.getSpectrumNumbers():
                i = self.wksp.getIndexFromSpectrumNumber(bank_number)
                datax, datay = self.wksp.dataX(i), self.wksp.dataY(i)

                bank_data = self.gen_figure_data(
                    i, name=f"{self.wksp.getName()} (Bank {bank_number})"
                )
                # setting plot limits
                self.minX = min(self.minX, datax.min())
                self.maxX = max(self.maxX, datax.max())
                self.minY = min(self.minX, datay.min())
                self.maxY = max(self.maxY, datay.max())

                # patching individual bank plot
                self.bragg_data_by_bank_dict[i]["data"] = bank_data["data"]
                self.bragg_data_by_bank_plots[i].object = self.bragg_data_by_bank_dict[
                    i
                ]

                traces.append(bank_data["data"])

            # setting slider limits
            self.xlim_slider.start = self.minX
            self.xlim_slider.end = self.xlim_slider.value = self.maxX
            self.ylim_slider.start = self.minY
            self.ylim_slider.end = self.ylim_slider.value = self.maxY
            # patching bragg data plot
            self.bragg_data_dict["data"] = traces
            self.bragg_data_dict["layout"].xaxis.range = [self.minX, 8.0]
            self.bragg_data_dict["layout"].yaxis.range = [self.minY, 3.0]
            self.bragg_data_dict["layout"].title.text = self.wksp_title
            self.bragg_data_plot.object = self.bragg_data_dict

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

    def update_main_layout(self, name):
        self.load_workspace(name)
        self.render_sidebar_content()
        self.render_main_content()

    def update_stateful_plot(self, file):
        # pull data from remote storage and display on a separate tab
        if file != "":
            traces = []
            wksp = load_gsas(os.path.join(STATEFUL_DATA_DIR, file))
            for bank_number in wksp.getSpectrumNumbers():
                i = wksp.getIndexFromSpectrumNumber(bank_number)
                dataX, dataY = wksp.dataX(i), wksp.dataY(i)
                traces.append(
                    go.Scatter(
                        x=dataX,
                        y=dataY,
                        name=f"{wksp.getName()} (Bank {i})",
                        line=dict(width=2),
                    )
                )
            epoch = int(wksp.getName().split("_")[0])
            human_readable_timestamp = datetime.fromtimestamp(
                epoch, tz=timezone.utc
            ).strftime("%A, %B %d, %Y %I:%M:%S %p UTC")

            self.stateful_plot_header_md.object = f"""
            <div style="border: 4px solid #005b8c; padding: 8px; background-color: #e0f0f7; display: inline-block; 
                border-radius: 15px; font-size: 18px; font-family: Arial, sans-serif;">
            <strong>Date:</strong> {human_readable_timestamp}
            </div>
            """

            self.stateful_plot_data_dict["data"] = traces
            self.stateful_plot_data_dict["layout"].xaxis.range = [0, 8.0]
            self.stateful_plot_data_dict["layout"].yaxis.range = [0, 3.0]
            self.stateful_plot_data_dict["layout"].title.text = (
                f"Bragg Data: {wksp.getName()}"
            )
            self.stateful_plot.object = self.stateful_plot_data_dict

    # LIFECYCLE METHODS
    def check_new_bragg_files(self):
        files = os.listdir(BRAGG_DIR)
        if files:
            files = sorted(files, key=lambda f: int(f.split("_")[0]))
            if files[-1] != self.current_bragg_file:
                self.current_bragg_file = files[-1]
                self.update_main_layout(files[-1])

            if len(files) > 1:
                for i in range(len(files) - 1):
                    filepath = os.path.join(BRAGG_DIR, files[i])
                    if os.path.exists(filepath):
                        os.remove(filepath)

    def check_new_transition_files(self):
        files = os.listdir(TRANSITION_DATA_DIR)
        if files:
            files = sorted(files, key=lambda f: int(f.split("_")[0]))
            if files[-1] != self.current_transition_file:
                self.current_transition_file = files[-1]
                self.render_transition_content(files[-1])

            if len(files) > 1:
                for i in range(len(files) - 1):
                    filepath = os.path.join(TRANSITION_DATA_DIR, files[i])
                    if os.path.exists(filepath):
                        os.remove(filepath)

    def check_new_next_temperature_files(self):
        files = os.listdir(NEXT_TEMPERATURE_DIR)
        if files:
            files = sorted(files, key=lambda f: int(f.split("_")[0]))
            if files[-1] != self.current_next_temperature_file:
                self.current_next_temperature_file = files[-1]
                with open(os.path.join(NEXT_TEMPERATURE_DIR, files[-1]), "r") as f:
                    for line in f:
                        temp = float(line.strip())
                        self.next_temperature = temp
                self.andie_header_md.object = f"""
                <div style="border: 4px solid #FBC02D;  padding: 8px; background-color: #FFF9C4; display: inline-block; 
                    border-radius: 15px; font-size: 18px; font-family: Arial, sans-serif;">
                <strong>ANDiE Next Temperature:</strong> {self.next_temperature} K
                </div>
                """
            if len(files) > 1:
                for i in range(len(files) - 1):
                    filepath = os.path.join(NEXT_TEMPERATURE_DIR, files[i])
                    if os.path.exists(filepath):
                        os.remove(filepath)

    def update_stateful_plot_list(self):
        self.files = self.load_stateful_files()
        self.select_bragg_file.options = self.files


def main():
    pn.extension("plotly")
    app_state = AppState()

    bragg_data_tab = pn.Column(
        pn.Row(app_state.all_banks_header_md, app_state.andie_header_md),
        app_state.bragg_data_plot,
    )

    by_bank_tab = pn.Column(
        pn.pane.Markdown("<h1>By Bank</h1>"),
        pn.GridBox(*app_state.bragg_data_by_bank_plots, ncols=3),
    )

    transition_plot_tab = pn.Column(
        pn.Row(app_state.all_banks_header_md, app_state.andie_header_md),
        app_state.transition_plot,
    )

    information_tab = pn.Row(app_state.wkspinfo_md)

    stateful_plots_tab = pn.Column(
        app_state.stateful_plot_header_md, app_state.stateful_plot
    )

    main = pn.Tabs(
        ("Bragg Data", bragg_data_tab),
        ("By Bank", by_bank_tab),
        ("Transition Plot", transition_plot_tab),
        ("Timestamp", stateful_plots_tab),
        ("Information", information_tab),
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
    )

    # Listen to changes in directory with period = DELAY secs
    pn.state.add_periodic_callback(
        callback=app_state.check_new_bragg_files, period=DELAY * 1000
    )
    pn.state.add_periodic_callback(
        callback=app_state.check_new_transition_files, period=DELAY * 1000
    )

    pn.state.add_periodic_callback(
        callback=app_state.check_new_next_temperature_files, period=DELAY * 1000
    )

    pn.state.add_periodic_callback(
        callback=app_state.update_stateful_plot_list, period=45 * 1000
    )

    template.servable()


main()
