"""
:author: Doug Skrypa
"""

from typing import Any, Optional

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .constants import DOMAIN


class NestFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        return self.async_create_entry(title='Raspberry Pi Sensor', data={})
