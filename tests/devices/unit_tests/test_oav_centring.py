import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
import pytest
from bluesky.run_engine import RunEngine
from ophyd.sim import make_fake_device

from dodal.devices.backlight import Backlight
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.oav_errors import OAVError_ZoomLevelNotFound
from dodal.devices.oav.oav_parameters import OAVParameters
from dodal.devices.smargon import Smargon

OAV_CENTRING_JSON = "tests/devices/unit_tests/test_OAVCentring.json"
DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


def do_nothing(*args):
    pass


@pytest.fixture
def mock_oav():
    oav: OAV = make_fake_device(OAV)(name="oav", prefix="a fake beamline")
    oav.wait_for_connection = do_nothing
    return oav


@pytest.fixture
def mock_parameters():
    return OAVParameters(OAV_CENTRING_JSON, ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION)


@pytest.fixture
def mock_smargon():
    smargon: Smargon = make_fake_device(Smargon)(name="smargon")
    smargon.wait_for_connection = do_nothing
    return smargon


@pytest.fixture
def mock_backlight():
    backlight: Backlight = make_fake_device(Backlight)(name="backlight")
    backlight.wait_for_connection = do_nothing
    return backlight


def test_can_make_fake_testing_devices_and_use_run_engine(
    mock_oav: OAV,
    mock_parameters: OAVParameters,
    mock_smargon: Smargon,
    mock_backlight: Backlight,
):
    @bpp.run_decorator()
    def fake_run(
        mock_oav: OAV,
        mock_parameters: OAVParameters,
        mock_smargon: Smargon,
        mock_backlight: Backlight,
    ):
        yield from bps.abs_set(mock_oav.cam.acquire_period, 5)
        mock_parameters.acquire_period = 10
        # can't change the smargon motors because of limit issues with FakeEpicsDevice
        # yield from bps.mv(mock_smargon.omega, 1)
        yield from bps.mv(mock_backlight.pos, 1)

    RE = RunEngine()
    RE(fake_run(mock_oav, mock_parameters, mock_smargon, mock_backlight))


@pytest.mark.parametrize(
    "parameter_name,expected_value",
    [("canny_edge_lower_threshold", 5.0), ("close_ksize", 11), ("direction", 1)],
)
def test_oav_parameters_load_parameters_from_json(
    parameter_name, expected_value, mock_parameters: OAVParameters
):

    mock_parameters.load_parameters_from_json()

    assert mock_parameters.__dict__[parameter_name] == expected_value


def test_oav__extract_dict_parameter_not_found_fallback_value_present(
    mock_parameters: OAVParameters,
):
    mock_parameters.load_json()
    assert (
        mock_parameters._extract_dict_parameter(
            "a_key_not_in_the_json", fallback_value=1
        )
        == 1
    )


def test_oav__extract_dict_parameter_not_found_fallback_value_not_present(
    mock_parameters: OAVParameters,
):
    mock_parameters.load_json()
    with pytest.raises(KeyError):
        mock_parameters._extract_dict_parameter("a_key_not_in_the_json")


@pytest.mark.parametrize(
    "zoom_level,expected_xCentre,expected_yCentre",
    [(1.0, 368, 365), (5.0, 383, 353), (10.0, 381, 335)],
)
def test_extract_beam_position_different_beam_postitions(
    zoom_level,
    expected_xCentre,
    expected_yCentre,
    mock_parameters: OAVParameters,
):
    mock_parameters.zoom = zoom_level
    mock_parameters._extract_beam_position()
    assert mock_parameters.beam_centre_x == expected_xCentre
    assert mock_parameters.beam_centre_y == expected_yCentre


@pytest.mark.parametrize(
    "zoom_level,expected_microns_x,expected_microns_y",
    [(2.5, 2.31, 2.31), (15.0, 0.302, 0.302)],
)
def test_load_microns_per_pixel_entries_found(
    zoom_level, expected_microns_x, expected_microns_y, mock_parameters: OAVParameters
):
    mock_parameters.load_microns_per_pixel(zoom_level)
    assert mock_parameters.micronsPerXPixel == expected_microns_x
    assert mock_parameters.micronsPerYPixel == expected_microns_y


def test_load_microns_per_pixel_entry_not_found(mock_parameters: OAVParameters):
    with pytest.raises(OAVError_ZoomLevelNotFound):
        mock_parameters.load_microns_per_pixel(0.000001)
