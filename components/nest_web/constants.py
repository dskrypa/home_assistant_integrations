from homeassistant.components.climate.const import HVAC_MODE_AUTO, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_OFF
from homeassistant.components.climate.const import CURRENT_HVAC_COOL, CURRENT_HVAC_HEAT, CURRENT_HVAC_IDLE
from homeassistant.components.climate.const import CURRENT_HVAC_FAN, PRESET_AWAY, PRESET_ECO, PRESET_NONE
from homeassistant.const import TEMP_FAHRENHEIT, TEMP_CELSIUS

DOMAIN = 'nest'
DATA_NEST = 'nest'
DATA_NEST_CONFIG = 'nest_config'
CONF_PROJECT_ID = 'project_id'
CONF_SUBSCRIBER_ID = 'subscriber_id'
SIGNAL_NEST_UPDATE = 'nest_update'
NEST_CONFIG_FILE = 'nest.conf'

DEVICES = 'devices'
METADATA = 'metadata'
STRUCTURES = 'structures'
THERMOSTATS = 'thermostats'
MINIMUM_TEMPERATURE_F = 50
MAXIMUM_TEMPERATURE_F = 90
MINIMUM_TEMPERATURE_C = 9
MAXIMUM_TEMPERATURE_C = 32
TEMP_UNIT_MAP = {'c': TEMP_CELSIUS, 'f': TEMP_FAHRENHEIT}

AWAY_MAP = {'on': 'away', 'away': 'away', 'off': 'home', 'home': 'home', True: 'away', False: 'home'}
FAN_MAP = {
    'auto on': False, 'on': True, 'auto': False, '1': True, '0': False, 1: True, 0: False, True: True, False: False
}

# region Climate Control
# NEST_MODE_HEAT_COOL = 'heat-cool'
NEST_MODE_HEAT_COOL = 'range'
NEST_MODE_ECO = 'eco'
NEST_MODE_HEAT = 'heat'
NEST_MODE_COOL = 'cool'
NEST_MODE_OFF = 'off'

MODE_HASS_TO_NEST = {
    HVAC_MODE_AUTO: NEST_MODE_HEAT_COOL,
    HVAC_MODE_HEAT: NEST_MODE_HEAT,
    HVAC_MODE_COOL: NEST_MODE_COOL,
    HVAC_MODE_OFF: NEST_MODE_OFF,
}

MODE_NEST_TO_HASS = {v: k for k, v in MODE_HASS_TO_NEST.items()}
ACTION_NEST_TO_HASS = {
    'off': CURRENT_HVAC_IDLE,
    'heating': CURRENT_HVAC_HEAT,
    'cooling': CURRENT_HVAC_COOL,
    'fan running': CURRENT_HVAC_FAN,
}
PRESET_AWAY_AND_ECO = 'Away and Eco'
PRESET_MODES = [PRESET_NONE, PRESET_AWAY, PRESET_ECO, PRESET_AWAY_AND_ECO]
# endregion

POLL_INTERVAL = 180
