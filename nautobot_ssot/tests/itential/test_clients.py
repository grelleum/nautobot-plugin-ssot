"""Itential SSoT API Client Tests."""

import os
from unittest import TestCase

from nautobot_ssot.tests.itential.fixtures import gateways


class AutomationGatewayClientTestCase(TestCase):
    """Itential Automation Gateway Client Test Cases."""

    def setUp(self):
        """Setup test cases."""
        for device in gateways.gateways:
            os.environ[device.get("username_env")] = "testUser"
            os.environ[device.get("password_env")] = "testPass"

            gateways.update_or_create_automation_gateways(
                name=device.get("name"),
                description=device.get("description"),
                location=device.get("location"),
                region=device.get("region"),
                gateway=device.get("gateway"),
                enabled=device.get("enabled"),
                username_env=device.get("username_env"),
                password_env=device.get("password_env"),
                secret_group=device.get("secret_group"),
            )

    def test_login(self):
        """Test API client login."""
        pass

    def test_logout(self):
        """Test API client logout."""
        pass

    def test_get_devices(self):
        """Test get_devices."""
        pass

    def test_get_device(self):
        """Test get_device."""
        pass

    def test_create_device(self):
        """Test create_device."""
        pass

    def test_update_device(self):
        """Test update_device."""
        pass

    def test_delete_device(self):
        """Test delete_device."""
        pass

    def test_get_groups(self):
        """Test get_groups."""
        pass

    def test_get_group(self):
        """Test get_group."""
        pass

    def test_create_group(self):
        """Test create_group."""
        pass

    def test_update_group(self):
        """Test update_group."""
        pass

    def test_delete_group(self):
        """Test delete_group."""
        pass

    def tearDown(self):
        """Teardown test cases."""
        pass
