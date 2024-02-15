import logging
import sys
from os import environ, getenv
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd.sim import make_fake_device

from dodal.beamlines import beamline_utils, i03
from dodal.devices.focusing_mirror import VFMMirrorVoltages
from dodal.log import LOGGER, GELFTCPHandler, set_up_logging_handlers

MOCK_DAQ_CONFIG_PATH = "tests/devices/unit_tests/test_daq_configuration"
mock_paths = [
    ("DAQ_CONFIGURATION_PATH", MOCK_DAQ_CONFIG_PATH),
    ("ZOOM_PARAMS_FILE", "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"),
    ("DISPLAY_CONFIG", "tests/devices/unit_tests/test_display.configuration"),
]
mock_attributes_table = {
    "i03": mock_paths,
    "s03": mock_paths,
    "i04": mock_paths,
    "s04": mock_paths,
}


def mock_beamline_module_filepaths(bl_name, bl_module):
    if mock_attributes := mock_attributes_table.get(bl_name):
        [bl_module.__setattr__(attr[0], attr[1]) for attr in mock_attributes]


def pytest_runtest_setup(item):
    beamline_utils.clear_devices()
    if LOGGER.handlers == []:
        mock_graylog_handler = MagicMock(spec=GELFTCPHandler)
        mock_graylog_handler.return_value.level = logging.DEBUG

        with patch("dodal.log.GELFTCPHandler", mock_graylog_handler):
            set_up_logging_handlers(None, False)


def pytest_runtest_teardown():
    if "dodal.beamlines.beamline_utils" in sys.modules:
        sys.modules["dodal.beamlines.beamline_utils"].clear_devices()


@pytest.fixture
def vfm_mirror_voltages() -> VFMMirrorVoltages:
    voltages = cast(
        VFMMirrorVoltages,
        make_fake_device(VFMMirrorVoltages)(
            name="vfm_mirror_voltages",
            prefix="BL-I03-MO-PSU-01:",
            daq_configuration_path=i03.DAQ_CONFIGURATION_PATH,
        ),
    )
    voltages.voltage_lookup_table_path = "tests/test_data/test_mirror_focus.json"
    return voltages


s03_epics_server_port = getenv("S03_EPICS_CA_SERVER_PORT")
s03_epics_repeater_port = getenv("S03_EPICS_CA_REPEATER_PORT")

if s03_epics_server_port is not None:
    environ["EPICS_CA_SERVER_PORT"] = s03_epics_server_port
    print(f"[EPICS_CA_SERVER_PORT] = {s03_epics_server_port}")
if s03_epics_repeater_port is not None:
    environ["EPICS_CA_REPEATER_PORT"] = s03_epics_repeater_port
    print(f"[EPICS_CA_REPEATER_PORT] = {s03_epics_repeater_port}")


@pytest.fixture
def RE():
    return RunEngine()
