"""
Initialize the Nest Web integration

:author: Doug Skrypa
"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from nest_client.client import NestWebClient

from .constants import DOMAIN, DATA_NEST_CONFIG, NEST_CONFIG_FILE, DATA_NEST
from .device import NestWebDevice

log = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Nest components with dispatch between old/new flows."""
    log.info(f'Beginning {DOMAIN} async_setup')
    hass.data[DOMAIN] = {}
    hass.data[DATA_NEST_CONFIG] = config.get(DOMAIN, {})
    log.info(f'Completed {DOMAIN} async_setup')
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nest from legacy config entry."""
    log.info(f'Beginning {DOMAIN} async_setup_entry')

    client = NestWebClient()
    conf = hass.data.get(DATA_NEST_CONFIG, {})
    hass.data[DATA_NEST] = NestWebDevice(hass, conf, client)

    await hass.data[DATA_NEST].initialize()
    # if not await hass.async_add_executor_job(hass.data[DATA_NEST].initialize):
    #     return False

    for module in ('climate', 'sensor'):
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, module))

    # entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, shut_down))
    log.info(f'Completed {DOMAIN} async_setup_entry')
    return True
