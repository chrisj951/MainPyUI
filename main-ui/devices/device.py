from typing import Optional

from devices.abstract_device import AbstractDevice


class Device:
    _impl: Optional[AbstractDevice] = None

    @staticmethod
    def init(impl: AbstractDevice):
        Device._impl = impl

    @staticmethod
    def get_device() -> AbstractDevice:
        if Device._impl is None:
            raise RuntimeError("Device not initialized")
        return Device._impl
