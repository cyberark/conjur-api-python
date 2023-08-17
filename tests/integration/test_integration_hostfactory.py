import asyncio
import json
import os

from aiounittest import AsyncTestCase

from conjur_api.errors.errors import HttpStatusError
from conjur_api.models.hostfactory.create_host_data import CreateHostData
from conjur_api.models.hostfactory.create_token_data import CreateTokenData
from tests.integration.integ_utils import create_client


class TestHostFactory(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    async def _create_host_token(self, c):
        token_data = \
            CreateTokenData(host_factory="factory", hours=1, cidr="0.0.0.0/0")
        token_response = await c.create_token(token_data)
        return token_response[0]['token']

    async def test_create_host_with_annotations(self):
        c = await create_client("admin", os.environ['CONJUR_AUTHN_API_KEY'])

        token = await self._create_host_token(c)

        self.assertEqual(
            1,
            len(token),
            f"Expecting one token got {len(token)}"
            )

        self.assertTrue(
            token[0].get('token') is not None,
            "Create token command did not produce a token"
        )

        host_data = CreateHostData(
                "new-host",
                token[0]['token'],
                {"creator": "me", "date": "today"}
            )

        response = await c.create_host(host_data)
        self.assertEqual('dev:host:new-host', response['id'])
        expected_annotations = \
            [
                {'name': 'creator', 'value': 'me'},
                {'name': 'date', 'value': 'today'}
            ]
        self.assertListEqual(expected_annotations, response['annotations'])

    async def test_fail_to_create_host(self):
        c = await create_client("admin", os.environ['CONJUR_AUTHN_API_KEY'])

        token = await self._create_host_token(c)
        host_data = \
            CreateHostData(
                "new-host",
                token,
                {"creator": "me", "date": "today"}
            )
        with self.assertRaises(HttpStatusError) as ex:
            await c.create_host(host_data)
        self.assertEqual(401, ex.exception.status)

    @classmethod
    async def _add_test_data(cls):
        c = await create_client("admin", os.environ['CONJUR_AUTHN_API_KEY'])
        await c.load_policy_file(
            "root",
            "tests/integration/policies/hostfactory.yml"
        )
