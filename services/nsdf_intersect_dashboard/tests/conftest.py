import pytest
import os


@pytest.fixture
def bragg_volume():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "bragg_volume"))


@pytest.fixture
def transition_volume():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "transition_volume"))


@pytest.fixture
def andie_volume():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "andie_volume"))


@pytest.fixture
def scientist_cloud_volume():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "scientist_cloud_volume"))
