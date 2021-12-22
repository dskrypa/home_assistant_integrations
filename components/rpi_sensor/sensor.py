"""
Nest Web thermostat sensors

:author: Doug Skrypa
"""

import logging
from functools import cached_property

from homeassistant.components.sensor import SensorEntity
# from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import PERCENTAGE, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RaspberryPiDevice
from .constants import DOMAIN, SIGNAL_UPDATE

log = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up a Nest sensor based on a config entry."""
    device = hass.data[DOMAIN]  # type: RaspberryPiDevice
    all_sensors = [cls(device, var) for cls in (RaspberryPiSensorDevice,) for var in cls._device_classes]
    async_add_entities(all_sensors, True)


class RaspberryPiSensorDevice(SensorEntity):
    _device_classes = {'humidity': DEVICE_CLASS_HUMIDITY, 'temperature': DEVICE_CLASS_TEMPERATURE}
    _units = {'humidity': PERCENTAGE, 'temperature': TEMP_CELSIUS}

    def __init__(self, device: RaspberryPiDevice, variable: str):
        self.device = device
        self.host = device.client.host
        self.variable = variable
        self._name = '{} {}'.format(self.host, variable.replace('_', ' '))
        self._state = None

    def _update_attrs(self):
        if (data := self.device.latest_data) is not None:
            value = data[self.variable]
            if self.variable == 'temperature':
                self._state = f'{value:.1f}'
            else:
                self._state = f'{value * 100:.1f}'

    @property
    def native_value(self):
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self) -> bool:
        return True

    @cached_property
    def unique_id(self):
        return f'{self.host}-{self.variable}'

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.host)},
            manufacturer='Raspberry Pi',
            model='2B',
            name='Raspberry Pi + DHT22',
            sw_version='2021.12.22-1',
        )

    @cached_property
    def device_class(self):
        return self._device_classes[self.variable]

    @property
    def native_unit_of_measurement(self):
        return self._units[self.variable]

    async def async_update(self):
        if await self.device.maybe_refresh():
            self._update_attrs()

    async def async_added_to_hass(self):
        """Register update signal handler."""

        async def async_update_state():
            """Update sensor state."""
            await self.async_update_ha_state(True)

        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_UPDATE, async_update_state))


# class RaspberryPiBinarySensor(RaspberryPiSensorDevice, BinarySensorEntity):
#     # TODO: is_pingable
