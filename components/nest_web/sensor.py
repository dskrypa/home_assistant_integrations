"""
Nest Web thermostat sensors

:author: Doug Skrypa
"""

import logging
from functools import cached_property

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import PERCENTAGE, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from nest_client.entities import Structure, ThermostatDevice, Shared

from .constants import DOMAIN, POLL_INTERVAL, SIGNAL_NEST_UPDATE, TEMP_UNIT_MAP, DATA_NEST
from .device import NestWebDevice

log = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up a Nest sensor based on a config entry."""
    log.info(f'Beginning {DOMAIN} async_setup_entry for sensor')
    nest = hass.data[DATA_NEST]  # type: NestWebDevice
    nest_web_dev = hass.data[DATA_NEST]

    all_sensors = [
        cls(nest_web_dev, structure, device, shared, var)
        for structure, device, shared in nest.struct_thermostat_groups
        # for cls in (NestBasicSensor, NestTempSensor, NestBinarySensor)
        for cls in (NestBasicSensor, NestBinarySensor)
        for var in cls._types
    ]
    async_add_entities(all_sensors, True)
    log.info(f'Completed {DOMAIN} async_setup_entry for sensor')


class NestSensorDevice(Entity):
    _types = {}
    device: ThermostatDevice

    def __init__(
        self, nest_web_dev: NestWebDevice, structure: Structure, device: ThermostatDevice, shared: Shared, variable: str
    ):
        self.nest_web_dev = nest_web_dev
        self.structure = structure
        self.variable = variable
        self.device = device
        self.shared = shared
        self._name = '{} {}'.format(device.description, variable.replace('_', ' '))
        self._state = None
        self._unit = None

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self) -> bool:
        return self.nest_web_dev.needs_refresh()
        # return any(obj.needs_refresh(POLL_INTERVAL) for obj in (self.structure, self.device, self.shared))

    @cached_property
    def unique_id(self):
        return f'{self.device.serial}-{self.variable}'

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        # if self.device.is_thermostat:
        #     model = 'Thermostat'
        # elif self.device.is_camera:
        #     model = 'Camera'
        # elif self.device.is_smoke_co_alarm:
        #     model = 'Nest Protect'
        # else:
        #     model = None
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.serial)},
            manufacturer='Nest',
            model='Thermostat',
            name=self.device.description,
            sw_version=self.device.software_version,
        )

    @cached_property
    def device_class(self):
        return self._types.get(self.variable)

    @property
    def native_unit_of_measurement(self):
        return self._unit

    async def async_update(self):
        """Do not use NestSensorDevice directly."""
        raise NotImplementedError

    async def async_added_to_hass(self):
        """Register update signal handler."""

        async def async_update_state():
            """Update sensor state."""
            await self.async_update_ha_state(True)

        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_NEST_UPDATE, async_update_state))


class NestBasicSensor(NestSensorDevice, SensorEntity):
    _types = {'humidity': DEVICE_CLASS_HUMIDITY, 'hvac_state': None}
    _units = {'humidity': PERCENTAGE}

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        await self.nest_web_dev.refresh()
        # await self.device.refresh()
        self._unit = self._units.get(self.variable)
        obj = self.device if self.variable == 'humidity' else self.shared
        self._state = getattr(obj, self.variable)


class NestTempSensor(NestSensorDevice, SensorEntity):
    _types = {'temperature': DEVICE_CLASS_TEMPERATURE, 'target_temperature': DEVICE_CLASS_TEMPERATURE}

    def __init__(
        self, nest_web_dev: NestWebDevice, structure: Structure, device: ThermostatDevice, shared: Shared, variable: str
    ):
        super().__init__(nest_web_dev, structure, device, shared, variable)
        # self._unit = TEMP_UNIT_MAP[self.device.client.config.temp_unit]
        self._unit = TEMP_CELSIUS

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        await self.nest_web_dev.refresh()
        # await self.device.refresh()
        shared = self.shared
        # Using _ versions to get raw celsius values
        if self.variable == 'target_temperature' and shared.target_temperature_type == 'range':
            # low, high = shared.target_temp_range
            low, high = shared._target_temp_range
            self._state = f'{low:.1f}-{high:.1f}'
        else:
            temp = shared._target_temperature if self.variable == 'target_temperature' else shared._current_temperature
            self._state = f'{temp:.1f}'


class NestBinarySensor(NestSensorDevice, BinarySensorEntity):
    _types = {
        'fan': 'running',
        # 'is_using_emergency_heat': 'heat',
        'has_leaf': None,
        'home': 'presence',
        'ac_running': 'cold',
        'heat_running': 'heat',
    }
    _negate = {'home'}
    _structure_var_attr_map = {'home': 'away'}
    _device_var_attr_map = {'has_leaf': 'leaf'}
    _shared_var_attr_map = {'fan': 'hvac_fan_state', 'heat_running': 'hvac_heater_state', 'ac_running': 'hvac_ac_state'}

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state

    @cached_property
    def _obj_and_attr(self):
        if attr := self._structure_var_attr_map.get(self.variable):
            return self.structure, attr
        elif attr := self._device_var_attr_map.get(self.variable):
            return self.device, attr
        elif attr := self._shared_var_attr_map.get(self.variable):
            return self.shared, attr

    async def async_update(self):
        await self.nest_web_dev.refresh()
        # await self.device.refresh()
        obj, attr = self._obj_and_attr
        value = getattr(obj, attr)
        self._state = not value if self.variable in self._negate else value
