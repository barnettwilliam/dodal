from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.turbo_slit import TurboSlit
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, get_hostname, skip_device

BL = get_beamline_name("i20_1")
set_log_beamline(BL)
set_utils_beamline(BL)


def _is_i20_1_machine():
    """
    Devices using PVA can only connect from i20_1 machines, due to the absence of
    PVA gateways at present.
    """
    hostname = get_hostname()
    return hostname.startswith("i20_1")


@skip_device(lambda: not _is_i20_1_machine())
def turbo_slit(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> TurboSlit:
    """Get the i20-1 motor"""

    return device_instantiation(
        TurboSlit,
        prefix="-OP-PCHRO-01:TS:",
        name="turbo_slit",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )
