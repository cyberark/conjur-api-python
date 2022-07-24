import unittest

from conjur_api.models import CreateHostData


class HostFactoryTest(unittest.TestCase):

    def test_create_host_data_fields(self):
        create_host_data = CreateHostData("1234", "token", {"creator": "john"})
        self.assertDictEqual({"id": "1234"}, create_host_data.get_host_id())
        self.assertDictEqual({"annotations[creator]": "john"}, create_host_data.get_annotations())
