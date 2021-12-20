"""
Nest Web thermostat control

:author: Doug Skrypa
"""

import logging

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW
from homeassistant.components.climate.const import SUPPORT_FAN_MODE, FAN_AUTO, FAN_ON
from homeassistant.components.climate.const import HVAC_MODE_AUTO, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_OFF
from homeassistant.components.climate.const import PRESET_AWAY, PRESET_NONE, SUPPORT_PRESET_MODE
from homeassistant.components.climate.const import SUPPORT_TARGET_TEMPERATURE, SUPPORT_TARGET_TEMPERATURE_RANGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from nest_client.exceptions import NestException
from nest_client.entities import Structure, ThermostatDevice

from .constants import DOMAIN, DATA_NEST, SIGNAL_NEST_UPDATE, ACTION_NEST_TO_HASS, POLL_INTERVAL
from .constants import NEST_MODE_HEAT_COOL, MODE_HASS_TO_NEST, MODE_NEST_TO_HASS, TEMP_UNIT_MAP

__all__ = ['NestThermostat', 'async_setup_entry']
log = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SCAN_INTERVAL, default=POLL_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=1))
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Nest climate device based on a config entry."""
    log.info(f'Beginning {DOMAIN} async_setup_entry for climate')
    temp_unit = hass.config.units.temperature_unit
    # hass.data[DATA_NEST] = NestWebDevice(hass, conf, nest)
    thermostats = await hass.async_add_executor_job(hass.data[DATA_NEST].thermostats)
    all_devices = [NestThermostat(structure, device, temp_unit) for structure, device in thermostats]
    async_add_entities(all_devices, True)
    log.info(f'Completed {DOMAIN} async_setup_entry for climate')


class NestThermostat(ClimateEntity):
    def __init__(self, structure: Structure, device: ThermostatDevice, temp_unit: str):
        self._unit = temp_unit
        self.structure = structure
        self.device = device
        self._fan_modes = [FAN_ON, FAN_AUTO]
        self._support_flags = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE
        if self.device.shared.can_heat and self.device.shared.can_cool:
            self._operation_list = [HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_OFF]
            self._support_flags |= SUPPORT_TARGET_TEMPERATURE_RANGE
        elif self.device.shared.can_heat:
            self._operation_list = [HVAC_MODE_HEAT, HVAC_MODE_OFF]
        elif self.device.shared.can_cool:
            self._operation_list = [HVAC_MODE_COOL, HVAC_MODE_OFF]
        else:
            self._operation_list = [HVAC_MODE_OFF]

        self._has_fan = self.device.has['fan']
        if self._has_fan:
            self._support_flags |= SUPPORT_FAN_MODE

        self._temperature_scale = TEMP_UNIT_MAP[self.device.client.config.temp_unit]
        self._away = None
        self._location = None
        self._name = None
        self._humidity = None
        self._target_temperature = None
        self._temperature = None
        self._mode = None
        self._action = None
        self._fan = None
        self._min_temperature = None
        self._max_temperature = None

    @property
    def should_poll(self) -> bool:
        return any(obj.needs_refresh(POLL_INTERVAL) for obj in (self.structure, self.device, self.device.shared))

    async def async_added_to_hass(self):
        """Register update signal handler."""

        async def async_update_state():
            """Update device state."""
            await self.async_update_ha_state(True)

        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_NEST_UPDATE, async_update_state))

    @property
    def supported_features(self):
        return self._support_flags

    @property
    def unique_id(self):
        return self.device.serial

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.serial)},
            manufacturer='Nest',
            model='Thermostat',
            name=self.device.description,
            sw_version=self.device.software_version,
        )

    @property
    def name(self):
        return self._name

    # region Temperature Properties / Methods

    @property
    def temperature_unit(self):
        return self._temperature_scale

    @property
    def min_temp(self):
        return self._min_temperature

    @property
    def max_temp(self):
        return self._max_temperature

    @property
    def current_temperature(self):
        return self._temperature

    @property
    def target_temperature(self):
        return self._target_temperature if self._mode != NEST_MODE_HEAT_COOL else None

    @property
    def target_temperature_low(self):
        return self._target_temperature[0] if self._mode == NEST_MODE_HEAT_COOL else None

    @property
    def target_temperature_high(self):
        return self._target_temperature[1] if self._mode == NEST_MODE_HEAT_COOL else None

    def set_temperature(self, **kwargs):
        try:
            self._set_temp(
                kwargs.get(ATTR_TARGET_TEMP_LOW), kwargs.get(ATTR_TARGET_TEMP_HIGH), kwargs.get(ATTR_TEMPERATURE)
            )
        except NestException as e:
            log.error(f'An error occurred while setting temperature: {e}')
            self.schedule_update_ha_state(True)  # restore target temperature

    def _set_temp(self, low, high, temp):
        if self._mode == NEST_MODE_HEAT_COOL and low is not None and high is not None:
            self.device.shared.set_temp_range(low, high)
        elif temp is not None:
            self.device.shared.set_temp(temp)
        else:
            log.debug(f'Invalid set_temperature args for mode={self._mode} - {low=} {high=} {temp=}')

    # endregion

    # region Mode Properties / Methods

    @property
    def hvac_modes(self):
        return self._operation_list

    @property
    def hvac_mode(self):
        return MODE_NEST_TO_HASS[self._mode]

    @property
    def hvac_action(self):
        return ACTION_NEST_TO_HASS[self._action]

    def set_hvac_mode(self, hvac_mode: str):
        self.device.shared.set_mode(MODE_HASS_TO_NEST[hvac_mode])

    @property
    def preset_mode(self):
        return PRESET_AWAY if self._away else PRESET_NONE

    @property
    def preset_modes(self) -> list[PRESET_NONE, PRESET_AWAY]:
        return [PRESET_NONE, PRESET_AWAY]

    def set_preset_mode(self, preset_mode: str):
        if preset_mode == self.preset_mode:
            return

        need_away = preset_mode == PRESET_AWAY
        is_away = self._away
        if is_away != need_away:
            self.structure.set_away(need_away)

    # endregion

    # region Fan Control

    @property
    def fan_mode(self):
        if self._has_fan:
            return FAN_ON if self._fan else FAN_AUTO
        # No Fan available so disable slider
        return None

    @property
    def fan_modes(self):
        return self._fan_modes if self._has_fan else None

    def set_fan_mode(self, fan_mode: str):
        if self._has_fan:
            if fan_mode == FAN_ON:
                self.device.start_fan()  # TODO: Set/Configure duration
            else:
                self.device.stop_fan()

    # endregion

    def update(self):
        log.info(f'[{DOMAIN}] Refreshing {self.device}')
        self.device.refresh()
        device, shared = self.device, self.device.shared
        self._location = device.where
        self._name = device.name
        self._humidity = device.humidity
        self._fan = device.fan
        self._away = self.structure.away
        self._temperature = shared.current_temperature
        self._mode = mode = shared.target_temperature_type
        self._target_temperature = shared.target_temp_range if mode == 'range' else shared.target_temperature
        self._action = shared.hvac_state
        self._min_temperature, self._max_temperature = shared.allowed_temp_range
