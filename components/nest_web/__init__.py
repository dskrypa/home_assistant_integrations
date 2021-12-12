"""

"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from nest.client import NestWebClient

from .constants import DOMAIN, DATA_NEST_CONFIG, NEST_CONFIG_FILE, DATA_NEST
from .device import NestWebDevice

log = logging.getLogger(__name__)
MODULES = ['climate', 'sensors']


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Nest components with dispatch between old/new flows."""
    hass.data[DOMAIN] = {}
    if DOMAIN not in config:
        return True

    # conf = config[DOMAIN]
    # filename = config.get(CONF_FILENAME, NEST_CONFIG_FILE)
    # access_token_cache_file = hass.config.path(filename)
    # hass.async_create_task(
    #     hass.config_entries.flow.async_init(
    #         DOMAIN, context={'source': SOURCE_IMPORT}, data={'nest_conf_path': access_token_cache_file}
    #     )
    # )

    # Store config to be used during entry setup
    # hass.data[DATA_NEST_CONFIG] = conf
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nest from legacy config entry."""
    client = NestWebClient()

    log.debug('proceeding with setup')
    conf = hass.data.get(DATA_NEST_CONFIG, {})
    hass.data[DATA_NEST] = NestWebDevice(hass, conf, client)
    if not await hass.async_add_executor_job(hass.data[DATA_NEST].initialize):
        return False

    for module in MODULES:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, module))

    # def validate_structures(target_structures):
    #     all_structures = {structure.name for structure in nest.structures}
    #     for target in target_structures:
    #         if target not in all_structures:
    #             log.info(f'Invalid structure={target}')

    # @callback
    # def start_up(event):
    #     """Start Nest update event listener."""
    #     threading.Thread(name='Nest update listener', target=nest_update_event_broker, args=(hass, nest)).start()
    #
    # hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, start_up)
    #
    # @callback
    # def shut_down(event):
    #     """Stop Nest update event listener."""
    #     nest.update_event.set()

    # entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, shut_down))
    log.debug('async_setup_nest is done')
    return True
