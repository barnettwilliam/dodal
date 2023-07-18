from ophyd import ADComponent as ADC
from ophyd import (
    AreaDetector,
    CamBase,
    Component,
    Device,
    EpicsSignal,
    HDF5Plugin,
    OverlayPlugin,
    ProcessPlugin,
    ROIPlugin,
    Signal,
    StatusBase,
)

from dodal.devices.areadetector.plugins.MXSC import MXSC
from dodal.devices.oav.grid_overlay import SnapshotWithGrid


class ZoomController(Device):
    """
    Device to control the zoom level. This should be set like
        >>> z = ZoomController(name="zoom")
        >>> z.set("1.0x")
        Status...
    """

    percentage: EpicsSignal = Component(EpicsSignal, "ZOOMPOSCMD")

    # Level is the string description of the zoom level e.g. "1.0x"
    level: EpicsSignal = Component(EpicsSignal, "MP:SELECT")
    # Used by OAV to work out if we're changing the setpoint
    _level_sp: Signal = Component(Signal)

    zrst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ZRST")
    onst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ONST")
    twst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.TWST")
    thst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.THST")
    frst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.FRST")
    fvst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.FVST")

    @property
    def allowed_zoom_levels(self):
        return [
            self.zrst.get(),
            self.onst.get(),
            self.twst.get(),
            self.thst.get(),
            self.frst.get(),
            self.fvst.get(),
        ]

    def set(self, level_to_set: str) -> StatusBase:
        self._level_sp.set(level_to_set)
        return self.level.set(level_to_set)


class OAV(AreaDetector):
    cam: CamBase = ADC(CamBase, "-DI-OAV-01:CAM:")
    roi: ROIPlugin = ADC(ROIPlugin, "-DI-OAV-01:ROI:")
    proc: ProcessPlugin = ADC(ProcessPlugin, "-DI-OAV-01:PROC:")
    over: OverlayPlugin = ADC(OverlayPlugin, "-DI-OAV-01:OVER:")
    tiff: OverlayPlugin = ADC(OverlayPlugin, "-DI-OAV-01:TIFF:")
    hdf5: HDF5Plugin = ADC(HDF5Plugin, "-DI-OAV-01:HDF5:")
    snapshot: SnapshotWithGrid = Component(SnapshotWithGrid, "-DI-OAV-01:MJPG:")
    mxsc: MXSC = ADC(MXSC, "-DI-OAV-01:MXSC:")
    zoom_controller: ZoomController = Component(ZoomController, "-EA-OAV-01:FZOOM:")

    def set_flatfield_on_zoom_level_one(self, value=None, old_value=None, **kwargs):
        flat_applied = self.proc.port_name.get()
        no_flat_applied = self.cam.port_name.get()

        input_plugin = flat_applied if value == "1.0x" else no_flat_applied

        self.mxsc.input_plugin.put(input_plugin)
        self.snapshot.input_plugin.put(input_plugin)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.zoom_controller._level_sp.subscribe(
            self.set_flatfield_on_zoom_level_one,
        )
