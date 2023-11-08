"""Test DiffSync IPAM models for Nautobot."""
from unittest.mock import MagicMock, patch
from django.contrib.contenttypes.models import ContentType
from diffsync import DiffSync
from nautobot.core.testing import TransactionTestCase
from nautobot.dcim.models import Device, DeviceType, Interface, Location, LocationType, Manufacturer, Platform
from nautobot.extras.models import Role, Status
from nautobot.ipam.models import IPAddress, IPAddressToInterface, Namespace, Prefix, VRF
from nautobot_ssot.integrations.device42.diffsync.models.nautobot import ipam


class TestNautobotVRFGroup(TransactionTestCase):
    """Test the NautobotVRFGroup class."""

    def setUp(self):
        self.diffsync = DiffSync()
        self.diffsync.namespace_map = {}
        self.diffsync.vrf_map = {}
        self.diffsync.job = MagicMock()
        self.diffsync.job.logger.info = MagicMock()
        self.vrf = VRF.objects.create(name="Test")
        self.vrf.validated_save()

    def test_create(self):
        """Validate the NautobotVRFGroup create() method creates a VRF."""
        self.vrf.delete()
        ids = {"name": "Test"}
        attrs = {"description": "Test VRF", "tags": ["test"], "custom_fields": {}}
        result = ipam.NautobotVRFGroup.create(self.diffsync, ids, attrs)
        self.assertIsInstance(result, ipam.NautobotVRFGroup)
        self.diffsync.job.logger.info.assert_called_once_with("Creating VRF Test.")
        namespace = Namespace.objects.get(name=ids["name"])
        self.assertEqual(namespace.name, ids["name"])
        self.assertEqual(self.diffsync.namespace_map[ids["name"]], namespace.id)
        vrf = VRF.objects.get(name=ids["name"])
        self.assertEqual(self.diffsync.vrf_map[ids["name"]], vrf.id)
        self.assertEqual(vrf.namespace.name, ids["name"])

    def test_update(self):
        """Validate the NautobotVRFGroup update() updates a VRF."""
        test_vrf = ipam.NautobotVRFGroup(
            name="Test", description="Test VRF", tags=["test"], custom_fields={}, uuid=self.vrf.id
        )
        test_vrf.diffsync = self.diffsync
        update_attrs = {"description": "Test VRF Update", "custom_fields": {"test": {"key": "test", "value": "test"}}}
        actual = ipam.NautobotVRFGroup.update(self=test_vrf, attrs=update_attrs)
        self.diffsync.job.logger.info.assert_called_once_with("Updating VRF Test.")
        self.vrf.refresh_from_db()
        self.assertEqual(self.vrf.description, update_attrs["description"])
        self.assertEqual(self.vrf.custom_field_data["test"], "test")
        self.assertEqual(actual, test_vrf)
        self.assertEqual(self.vrf.description, "Test VRF Update")
        self.assertEqual(self.vrf.custom_field_data["test"], "test")

    @patch(
        "nautobot_ssot.integrations.device42.diffsync.models.nautobot.ipam.PLUGIN_CFG",
        {"device42_delete_on_sync": True},
    )
    @patch("nautobot_ssot.integrations.device42.diffsync.models.nautobot.ipam.OrmVRF.objects.get")
    def test_delete(self, mock_vrf):
        """Validate the NautobotVRFGroup delete() deletes a VRF."""
        vrf_group = ipam.NautobotVRFGroup(
            name="Test", description=None, tags=None, custom_fields=None, uuid=self.vrf.id
        )
        vrf_group.diffsync = self.diffsync
        mock_vrf.return_value = self.vrf
        self.diffsync.objects_to_delete = {"vrf": []}

        vrf_group.delete()

        self.diffsync.job.logger.info.assert_called_once_with("VRF Test will be deleted.")
        self.assertEqual(len(self.diffsync.objects_to_delete["vrf"]), 1)
        self.assertEqual(self.diffsync.objects_to_delete["vrf"][0].id, self.vrf.id)


class TestNautobotSubnet(TransactionTestCase):
    """Test the NautobotSubnet class."""

    def setUp(self):
        super().setUp()
        self.status_active = Status.objects.get(name="Active")
        self.test_ns = Namespace.objects.get_or_create(name="Test")[0]
        self.test_vrf = VRF.objects.get_or_create(name="Test", namespace=self.test_ns)[0]
        self.prefix = Prefix.objects.create(prefix="10.0.0.0/24", namespace=self.test_ns, status=self.status_active)
        self.diffsync = DiffSync()
        self.diffsync.namespace_map = {"Test": self.test_ns.id}
        self.diffsync.vrf_map = {"Test": self.test_vrf.id}
        self.diffsync.status_map = {"Active": self.status_active.id}
        self.diffsync.prefix_map = {}
        self.diffsync.job = MagicMock()
        self.diffsync.job.logger.info = MagicMock()

    def test_create(self):
        """Validate the NautobotSubnet create() method creates a Prefix."""
        self.prefix.delete()
        ids = {"network": "10.0.0.0", "mask_bits": "24", "vrf": "Test"}
        attrs = {"description": "", "tags": [], "custom_fields": {}}
        result = ipam.NautobotSubnet.create(self.diffsync, ids, attrs)
        self.assertIsInstance(result, ipam.NautobotSubnet)
        self.diffsync.job.logger.info.assert_called_once_with("Creating Prefix 10.0.0.0/24 in VRF Test.")
        subnet = Prefix.objects.get(prefix=f"{ids['network']}/{ids['mask_bits']}", namespace=self.test_ns)
        self.assertEqual(str(subnet.prefix), f"{ids['network']}/{ids['mask_bits']}")
        self.assertEqual(self.diffsync.prefix_map["Test"][f"{ids['network']}/{ids['mask_bits']}"], subnet.id)
        self.assertEqual(subnet.vrfs.all().first(), self.test_vrf)

    def test_update(self):
        """Validate the NautobotSubnet update() method updates a Prefix."""
        test_pf = ipam.NautobotSubnet(
            network="10.0.0.0",
            mask_bits=24,
            description=None,
            vrf="Test",
            tags=[],
            custom_fields={},
            uuid=self.prefix.id,
        )
        test_pf.diffsync = self.diffsync
        update_attrs = {
            "description": "Test Prefix",
            "tags": ["test"],
            "custom_fields": {"test": {"key": "test", "value": "test"}},
        }
        actual = ipam.NautobotSubnet.update(self=test_pf, attrs=update_attrs)
        self.diffsync.job.logger.info.assert_called_once_with("Updating Prefix 10.0.0.0/24.")
        self.prefix.refresh_from_db()
        self.assertEqual(self.prefix.description, "Test Prefix")
        self.assertEqual(actual, test_pf)

    @patch(
        "nautobot_ssot.integrations.device42.diffsync.models.nautobot.ipam.PLUGIN_CFG",
        {"device42_delete_on_sync": True},
    )
    @patch("nautobot_ssot.integrations.device42.diffsync.models.nautobot.ipam.OrmPrefix.objects.get")
    def test_delete(self, mock_subnet):
        """Validate the NautobotVRFGroup delete() deletes a Prefix."""
        test_pf = ipam.NautobotSubnet(
            network="10.0.0.0",
            mask_bits=24,
            description=None,
            vrf="Test",
            tags=None,
            custom_fields=None,
            uuid=self.prefix.id,
        )
        test_pf.diffsync = self.diffsync
        mock_subnet.return_value = self.prefix
        self.diffsync.objects_to_delete = {"subnet": []}

        test_pf.delete()

        self.diffsync.job.logger.info.assert_called_once_with("Prefix 10.0.0.0/24 will be deleted.")
        self.assertEqual(len(self.diffsync.objects_to_delete["subnet"]), 1)
        self.assertEqual(self.diffsync.objects_to_delete["subnet"][0].id, self.prefix.id)


class TestNautobotIPAddress(TransactionTestCase):  # pylint: disable=too-many-instance-attributes
    """Test the NautobotIPAddress class."""

    def __init__(self, *args, **kwargs):
        """Initialize shared variables."""
        super().__init__(*args, **kwargs)
        self.addr = None

    def setUp(self):
        super().setUp()
        self.status_active = Status.objects.get(name="Active")
        status_reserved = Status.objects.get(name="Reserved")
        loc_type = LocationType.objects.get_or_create(name="Site")[0]
        loc_type.content_types.add(ContentType.objects.get_for_model(Device))
        loc = Location.objects.get_or_create(name="Test Site", location_type=loc_type, status=self.status_active)[0]
        cisco_manu = Manufacturer.objects.get_or_create(name="Cisco")[0]
        csr1000v = DeviceType.objects.get_or_create(model="CSR1000v", manufacturer=cisco_manu)[0]
        ios_platform = Platform.objects.create(name="Cisco IOS", manufacturer=cisco_manu)
        router_role = Role.objects.create(name="Router")
        router_role.content_types.add(ContentType.objects.get_for_model(Device))
        self.test_dev = Device.objects.create(
            name="Test Device",
            device_type=csr1000v,
            location=loc,
            platform=ios_platform,
            role=router_role,
            status=self.status_active,
        )
        self.test_dev2 = Device.objects.create(
            name="Device2",
            device_type=csr1000v,
            location=loc,
            platform=ios_platform,
            role=router_role,
            status=self.status_active,
        )
        self.dev_eth0 = Interface.objects.create(
            name="eth0", type="virtual", device=self.test_dev, status=self.status_active, mgmt_only=True
        )
        self.dev2_eth0 = Interface.objects.create(
            name="eth0", type="virtual", device=self.test_dev2, status=self.status_active, mgmt_only=True
        )
        self.dev2_mgmt = Interface.objects.create(
            name="mgmt0", type="virtual", device=self.test_dev2, status=self.status_active, mgmt_only=True
        )
        self.test_ns = Namespace.objects.get_or_create(name="Test")[0]
        self.prefix = Prefix.objects.create(
            prefix="10.0.0.0/24",
            location=loc,
            namespace=self.test_ns,
            status=self.status_active,
        )
        self.ids = {"address": "10.0.0.1/24", "subnet": "10.0.0.0/24"}
        self.attrs = {
            "namespace": "Test",
            "available": False,
            "label": "Test",
            "device": "Test Device",
            "interface": "eth0",
            "primary": True,
            "tags": [],
            "custom_fields": {},
        }

        self.diffsync = DiffSync()
        self.diffsync.namespace_map = {"Test": self.test_ns.id}
        self.diffsync.status_map = {"Active": self.status_active.id, "Reserved": status_reserved.id}
        self.diffsync.prefix_map = {"10.0.0.0/24": self.prefix.id}
        self.diffsync.device_map = {"Test Device": self.test_dev.id}
        self.diffsync.port_map = {
            "Test Device": {"eth0": self.dev_eth0.id},
            "Device2": {"mgmt0": self.dev2_mgmt.id, "eth0": self.dev2_eth0.id},
        }
        self.diffsync.ipaddr_map = {}
        self.diffsync.job = MagicMock()
        self.diffsync.job.logger.info = MagicMock()
        self.mock_addr = ipam.NautobotIPAddress(**self.ids, **self.attrs)
        self.mock_addr.diffsync = self.diffsync

    def test_create_with_existing_interface(self):
        """Validate the NautobotIPAddress.create() functionality with existing Interface."""
        result = ipam.NautobotIPAddress.create(self.diffsync, self.ids, self.attrs)
        self.assertIsInstance(result, ipam.NautobotIPAddress)
        self.diffsync.job.logger.info.assert_called_once_with("Creating IPAddress 10.0.0.1/24.")
        ipaddr = IPAddress.objects.get(address=self.ids["address"])
        self.assertEqual(ipaddr.parent, self.prefix)
        self.assertEqual(str(ipaddr.address), self.ids["address"])
        ipaddr_to_intf = IPAddressToInterface(ip_address=ipaddr, interface=self.dev_eth0)
        self.assertEqual(ipaddr_to_intf.interface, self.dev_eth0)
        self.assertEqual(self.diffsync.ipaddr_map["Test"][self.ids["address"]], ipaddr.id)
        self.test_dev.refresh_from_db()
        self.assertEqual(self.test_dev.primary_ip4, ipaddr)

    def test_create_with_missing_prefix(self):
        """Validate the NautobotIPAddress.create() functionality with missing Prefix."""
        self.prefix.delete()
        self.diffsync.job.logger.error = MagicMock()
        result = ipam.NautobotIPAddress.create(self.diffsync, self.ids, self.attrs)
        self.diffsync.job.logger.error.assert_called_once_with(
            "Unable to find prefix 10.0.0.0/24 to create IPAddress 10.0.0.1/24 for."
        )
        self.assertIsNone(result)

    def test_create_with_missing_interface(self):
        """Validate the NautobotIPAddress.create() functionality with missing Interface."""
        self.diffsync.port_map = {}
        self.diffsync.job.logger.debug = MagicMock()
        result = ipam.NautobotIPAddress.create(self.diffsync, self.ids, self.attrs)
        self.diffsync.job.logger.debug.assert_called_once_with("Unable to find Interface eth0 for Test Device.")
        self.assertIsInstance(result, ipam.NautobotIPAddress)

    def create_mock_ipaddress_and_assign(self):
        """Create IPAddress from mock_addr object and assign ID from IPAddress object that's created."""
        self.mock_addr.create(diffsync=self.diffsync, ids=self.ids, attrs=self.attrs)
        self.addr = IPAddress.objects.get(address="10.0.0.1/24")
        self.mock_addr.uuid = self.addr.id

    def test_update_changing_available(self):
        """Validate the NautobotIPAddress.update() functionality with changing available status."""
        self.create_mock_ipaddress_and_assign()
        update_attrs = {"available": True}
        ipam.NautobotIPAddress.update(self=self.mock_addr, attrs=update_attrs)
        self.addr.refresh_from_db()
        self.assertEqual(self.addr.status, self.status_active)

    def test_update_changing_label(self):
        """Validate the NautobotIPAddress.update() functionality with changing label."""
        self.create_mock_ipaddress_and_assign()
        update_attrs = {"label": "Test Update"}
        ipam.NautobotIPAddress.update(self=self.mock_addr, attrs=update_attrs)
        self.addr.refresh_from_db()
        self.assertEqual(self.addr.description, update_attrs["label"])

    def test_update_changing_interface(self):
        """Validate the NautobotIPAddress.update() functionality with changing Interface."""
        self.create_mock_ipaddress_and_assign()
        update_attrs = {
            "device": "Device2",
            "interface": "mgmt0",
            "primary": True,
        }
        result = ipam.NautobotIPAddress.update(self=self.mock_addr, attrs=update_attrs)
        self.assertIsInstance(result, ipam.NautobotIPAddress)
        self.test_dev2.refresh_from_db()
        self.assertEqual(self.test_dev2.primary_ip4, self.addr)
        ip_to_intfs = IPAddressToInterface.objects.filter(ip_address=self.addr, interface=self.dev2_mgmt)
        self.assertEqual(len(ip_to_intfs), 1)

    def test_update_changing_device(self):
        """Validate the NautobotIPAddress.update() functionality with changing Device."""
        self.create_mock_ipaddress_and_assign()
        update_attrs = {"device": "Device2"}
        result = ipam.NautobotIPAddress.update(self=self.mock_addr, attrs=update_attrs)
        self.assertIsInstance(result, ipam.NautobotIPAddress)
        self.addr.refresh_from_db()
        self.test_dev2.refresh_from_db()
        self.assertEqual(self.test_dev2.primary_ip4, self.addr)
        ip_to_intf = IPAddressToInterface.objects.filter(ip_address=self.addr, interface=self.dev2_eth0)
        self.assertEqual(len(ip_to_intf), 1)
