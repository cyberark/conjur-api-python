import asyncio
import json

import pytest
from aiounittest import AsyncTestCase

from conjur_api.errors.errors import HttpStatusError
from conjur_api.models.hostfactory.create_host_data import CreateHostData
from conjur_api.models.hostfactory.create_token_data import CreateTokenData
from tests.integration.integ_utils import create_admin_client


@pytest.mark.integration
class TestHostFactory(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    async def test_create_host_with_annotations(self):
        c = await create_admin_client()

        token: json = await c.create_token(CreateTokenData(host_factory="factory", hours=1, cidr="0.0.0.0/0"))
        self.assertEqual(1, len(token), f"Expecting one token got {len(token)}")
        self.assertTrue(token[0].get('token') is not None, "Create token command did not produce a token")
        response = await c.create_host(CreateHostData("new-host", token[0]['token'], {"creator": "me", "date": "today"}))
        self.assertEqual('conjur:host:new-host', response['id'])
        self.assertListEqual([{'name': 'creator', 'value': 'me'}, {'name': 'date', 'value': 'today'}], response['annotations'])

    async def test_fail_to_create_host(self):
        c = await create_admin_client()

        token: json = await c.create_token(CreateTokenData(host_factory="factory", hours=1, cidr="0.0.0.0/32"))
        with self.assertRaises(HttpStatusError) as ex:
            await c.create_host(CreateHostData("new-host", token[0]['token'], {"creator": "me", "date": "today"}))
        self.assertEqual(401, ex.exception.status)


    @classmethod
    async def _add_test_data(cls):
        c = await create_admin_client()
        await c.update_policy_file("root", "tests/integration/policies/hostfactory.yml")
