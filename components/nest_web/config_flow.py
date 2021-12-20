"""
Config flow to configure Nest.
"""

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .constants import DOMAIN

log = logging.getLogger(__name__)


class NestFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        log.info(f'Beginning {DOMAIN} NestFlowHandler.async_step_user')
        return self.async_create_entry(title='Nest Web', data={})
