"""
Initialize the Nest Web integration

:author: Doug Skrypa
"""

import logging
from asyncio import Lock
from datetime import datetime, timedelta

from httpx import HTTPError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from requests_client.async_client import AsyncRequestsClient

from .constants import DOMAIN, DATA_CONFIG

log = logging.getLogger(__name__)
DEFAULT_REFRESH_INTERVAL = 30
MIN_REFRESH_INTERVAL = timedelta(seconds=5)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Nest components with dispatch between old/new flows."""
    hass.data[DOMAIN] = {}
    hass.data[DATA_CONFIG] = config.get(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nest from legacy config entry."""
    conf = hass.data.get(DATA_CONFIG, {})

    hass.data[DOMAIN] = device = RaspberryPiDevice(hass, conf)
    success = await device.initialize()
    if not success:
        return False

    for module in ('sensor',):
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, module))

    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    device = hass.data[DOMAIN]  # type: RaspberryPiDevice
    await device.aclose()


class RaspberryPiDevice:
    client: AsyncRequestsClient

    def __init__(self, hass: HomeAssistant, conf):
        """Init Nest Devices."""
        self.hass = hass
        self.conf = conf
        self.refresh_interval = timedelta(seconds=int(conf.get('refresh_interval', DEFAULT_REFRESH_INTERVAL)))
        if self.refresh_interval < MIN_REFRESH_INTERVAL:
            log.warning(f'Invalid {DOMAIN}.refresh_interval = {self.refresh_interval} - using default')
            self.refresh_interval = timedelta(seconds=DEFAULT_REFRESH_INTERVAL)

        self.refresh_lock = Lock()
        self.last_refresh = datetime.now() - self.refresh_interval
        self.latest_data = None

    async def initialize(self):
        log.info('Beginning RaspberryPiDevice.initialize')
        try:
            net_loc = self.conf['net_loc']
        except KeyError:
            log.warning('Missing required config key=net_loc')
            return False

        self.client = AsyncRequestsClient(net_loc)
        log.info('Finished RaspberryPiDevice.initialize')
        return True

    def needs_refresh(self) -> bool:
        return (datetime.now() - self.last_refresh) >= self.refresh_interval

    async def maybe_refresh(self) -> bool:
        if not self.needs_refresh():
            log.debug('Refresh is not currently necessary')
            return False
        else:
            await self.refresh()
            return True

    async def refresh(self):
        log.debug('Beginning refresh')
        async with self.refresh_lock:
            log.debug('Acquired refresh lock')
            delta = datetime.now() - self.last_refresh
            delta_str = format_duration(delta.total_seconds())
            log.debug(f'Last refresh was delta={delta_str} ago')
            if delta < MIN_REFRESH_INTERVAL:
                log.debug(f'Skipping refresh - last_refresh={self.last_refresh.isoformat(" ")}')
                return

            try:
                resp = await self.client.get('read')
            except HTTPError as e:
                log.error(f'Error retrieving latest status: {e}')
            else:
                self.latest_data = resp.json()
            log.debug('Refresh is done')
            self.last_refresh = datetime.now()

    async def aclose(self):
        await self.client.aclose()


def format_duration(seconds: float) -> str:
    """
    Formats time in seconds as (Dd)HH:MM:SS (time.stfrtime() is not useful for formatting durations).

    :param seconds: Number of seconds to format
    :return: Given number of seconds as (Dd)HH:MM:SS
    """
    x = '-' if seconds < 0 else ''
    m, s = divmod(abs(seconds), 60)
    h, m = divmod(int(m), 60)
    d, h = divmod(h, 24)
    x = f'{x}{d}d' if d > 0 else x
    return f'{x}{h:02d}:{m:02d}:{s:02d}' if isinstance(s, int) else f'{x}{h:02d}:{m:02d}:{s:05.2f}'
