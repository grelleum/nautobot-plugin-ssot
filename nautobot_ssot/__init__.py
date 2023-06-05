"""Plugin declaration for nautobot_ssot."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added

try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

from nautobot.extras.plugins import PluginConfig

from .integrations.utils import each_enabled_integration_module
from .utils import logger

__version__ = metadata.version(__name__)


class NautobotSSOTPluginConfig(PluginConfig):
    """Plugin configuration for the nautobot_ssot plugin."""

    name = "nautobot_ssot"
    verbose_name = "Single Source of Truth"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot App that enables Single Source of Truth.  Allows users to aggregate distributed data sources and/or distribute Nautobot data to other data sources such as databases and SDN controllers."
    base_url = "ssot"
    required_settings = []
    min_version = "1.4.0"
    max_version = "1.9999"
    default_settings = {
        "hide_example_jobs": True,
    }
    caching_config = {}

    def ready(self):
        """Trigger callback when database is ready."""
        super().ready()

        for module in each_enabled_integration_module("signals"):
            logger.debug("Registering signals for %s", module.__file__)
            module.register_signals(self)


config = NautobotSSOTPluginConfig  # pylint:disable=invalid-name
