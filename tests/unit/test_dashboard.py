"""
File: test_dashboard.py
Author: NSDF-INTERSECT Team
License: BSD-3
Description: Unit tests for the dashboard.
"""

from __future__ import annotations
import os
from services import AppState, App
import pytest


@pytest.fixture
def bragg_volume():
    return "./tests/fixtures/bragg_volume"


@pytest.fixture
def transition_volume():
    return "./tests/fixtures/transition_volume"


@pytest.fixture
def andie_volume():
    return "./tests/fixtures/andie_volume"


@pytest.fixture
def scientist_cloud_volume():
    return "./tests/fixtures/scientist_cloud_volume"


@pytest.fixture
def configured_app(
    bragg_volume, transition_volume, andie_volume, scientist_cloud_volume
) -> AppState:
    app = AppState()
    app.config["volumes"]["bragg_volume"] = bragg_volume
    app.config["volumes"]["transition_volume"] = transition_volume
    app.config["volumes"]["andie_volume"] = andie_volume
    app.config["volumes"]["scientist_cloud_volume"] = scientist_cloud_volume
    return app


@pytest.fixture
def unconfigured_app() -> AppState:
    app = AppState()
    return app


class TestInitialization:
    def test_init_with_no_config(self, caplog: pytest.LogCaptureFixture):
        with pytest.raises(FileNotFoundError) as ex:
            App()
        assert ex.type is FileNotFoundError
        assert (
            "could not initialize dashboard, configuration path does not exists:"
            in caplog.text
        )


class TestPollingMethods:
    def test_no_volume_poll_bragg(
        self, unconfigured_app, caplog: pytest.LogCaptureFixture
    ):
        unconfigured_app.poll_bragg()
        assert "Bragg volume:  not found, skipping checks..." in caplog.text

    def test_poll_bragg(self, configured_app, bragg_volume):
        configured_app.poll_bragg()
        assert configured_app.current_bragg_file == "1743619484_NOM168366tof.gsa"
        assert len(os.listdir(bragg_volume)) == 1

    def test_no_volume_poll_transition(
        self, unconfigured_app, caplog: pytest.LogCaptureFixture
    ):
        unconfigured_app.poll_transition()
        assert "Transition volume:  not found, skipping checks..." in caplog.text

    def test_poll_transition(self, configured_app, transition_volume):
        configured_app.poll_transition()
        assert configured_app.id_campaign == "cb199084-91ec-4b9b-898d-024d1920b8cb"
        assert configured_app.id_transition == "6fb0c800-b960-4af7-a6e1-3ebbf73c2a6d"
        assert len(os.listdir(transition_volume)) == 1

    def test_no_volume_poll_andie(
        self, unconfigured_app, caplog: pytest.LogCaptureFixture
    ):
        unconfigured_app.poll_andie()
        assert "ANDiE volume:  not found, skipping checks..." in caplog.text

    def test_poll_andie(self, configured_app):
        configured_app.poll_andie()
        assert configured_app.id_andie == "8cdcb065-4b0f-4473-bfb7-d715965f8e13"


class TestLoaders:
    def test_load_stateful_files(self, configured_app):
        timestamp_to_filename = configured_app._load_stateful_files()
        assert len(timestamp_to_filename) == 5

    def test_load_workspace(self, configured_app):
        configured_app._load_workspace("1743619484_NOM168366tof.gsa")
        assert len(configured_app.bragg_data.keys()) == 6
        assert len(configured_app.bragg_data[1]) == 3


class TestRenderers:
    def test_render_bragg_plot(self, configured_app):
        configured_app.poll_bragg()
        configured_app._render_bragg_plot()
        assert len(configured_app.bragg_data_by_bank) == 6
        assert len(configured_app.bragg_data_dict["data"]) == 6
        assert configured_app.all_banks_header_md != """"""
        assert configured_app.bragg_data_dict["layout"].title.text != ""
        assert configured_app.minX >= 0.0
        assert configured_app.minY >= 0.0

    def test_render_transition_content(self, configured_app):
        configured_app.poll_transition()
        configured_app._render_transition_content()
        assert len(configured_app.transition_data_dict["data"]) == 3
        # The last trace in the transition content should always be the ANDiE prediction trace
        assert (
            configured_app.transition_data_dict["data"][-1].name
            == "ANDiE Next Temperature"
        )
        assert (
            "cb199084-91ec-4b9b-898d-024d1920b8cb"
            in configured_app.transition_data_dict["layout"].title.text
        )

    def test_render_andie_content(self, configured_app):
        configured_app.poll_andie()
        configured_app._render_andie_content()
        assert len(configured_app.transition_data_dict["data"]) > 0
        assert (
            configured_app.transition_data_dict["data"][-1].name
            == "ANDiE Next Temperature"
        )
        assert configured_app.andie_header_md != """"""

    def test_render_information_content(self, configured_app):
        configured_app._render_information_content()
        assert configured_app.information_md != """"""


class TestReactivity:
    def test_update_stateful_plot(self, configured_app):
        configured_app.update_stateful_plot("1743619479_NOM168364tof.gsa")
        assert configured_app.stateful_plot_header_md != """"""
        assert len(configured_app.stateful_plot_data_dict["data"]) > 0
        assert (
            "1743619479_NOM168364tof"
            in configured_app.stateful_plot_data_dict["layout"].title.text
        )

    def test_reset_limits(self, configured_app):
        configured_app.maxX = 10.0
        configured_app.maxY = 15.0
        configured_app.reset_limits("")
        assert configured_app.xlim_slider.value >= 10.0
        assert configured_app.ylim_slider.value >= 15.0

    def test_update_x_limit(self, configured_app):
        configured_app.update_x_limit(10)
        assert configured_app.bragg_data_dict["layout"].xaxis.range[1] == 10

    def test_update_y_limit(self, configured_app):
        configured_app.update_y_limit(10)
        assert configured_app.bragg_data_dict["layout"].yaxis.range[1] == 10


class TestHelpers:
    def test_last_id(self, configured_app):
        last_id_transition = configured_app._last_id(
            "TRANSITION", "cb199084-91ec-4b9b-898d-024d1920b8cb_transition.txt"
        )
        last_id_andie = configured_app._last_id("ANDIE", "")
        assert last_id_transition == "6fb0c800-b960-4af7-a6e1-3ebbf73c2a6d"
        assert last_id_andie == "8cdcb065-4b0f-4473-bfb7-d715965f8e13"
