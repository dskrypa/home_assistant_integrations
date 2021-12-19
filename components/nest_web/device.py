"""

"""

import logging
from typing import Iterator

from homeassistant.const import CONF_STRUCTURE
from homeassistant.core import HomeAssistant

from nest_client.client import NestWebClient
from nest_client.exceptions import NestException
from nest_client.entities import Structure, ThermostatDevice, NestDevice

from .constants import DOMAIN

__all__ = ['NestWebDevice']
log = logging.getLogger(__name__)


class NestWebDevice:
    def __init__(self, hass: HomeAssistant, conf, nest: NestWebClient):
        """Init Nest Devices."""
        self.hass = hass
        self.nest = nest
        self.local_structure = conf.get(CONF_STRUCTURE)

    def initialize(self):
        log.info(f'[{DOMAIN}] Beginning NestWebDevice.initialize')
        try:
            # Do not optimize the next statement - it is here to initialize the Nest API connection.
            structure_names = {s.name for s in self.nest.structures}
            if self.local_structure is None:
                self.local_structure = structure_names
        except NestException as e:
            log.error(f'Connection error while access Nest web service: {e}')
            return False
        return True

    def structures(self) -> Iterator[Structure]:
        try:
            for structure in self.nest.structures:
                if structure.name not in self.local_structure:
                    log.debug(f'Ignoring {structure=} - not in {self.local_structure}')
                    continue
                yield structure
        except NestException as e:
            log.error(f'Connection error while accessing Nest web service: {e}')

    def thermostats(self) -> Iterator[tuple[Structure, ThermostatDevice]]:
        return self._devices('thermostats')

    def _devices(self, device_type: str) -> Iterator[tuple[Structure, NestDevice]]:
        try:
            for structure in self.nest.structures:
                if structure.name not in self.local_structure:
                    log.debug(f'Ignoring {structure=} - not in {self.local_structure}')
                    continue

                for device in getattr(structure, device_type, ()):
                    yield structure, device
        except NestException as e:
            log.error(f'Connection error while access Nest web service: {e}')
