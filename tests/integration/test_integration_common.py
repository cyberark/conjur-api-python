import asyncio

import pytest
from aiounittest import AsyncTestCase

from tests.integration.integ_utils import create_admin_client


@pytest.mark.integration
@pytest.mark.cloud
class TestIntegrationCommon(AsyncTestCase):
  '''
  Common integration tests for Conjur API. They test the basic functionality
  of the API and can run against any Conjur flavor, including Conjur Cloud.
  '''

  @classmethod
  def setUpClass(cls):
    asyncio.run(cls._add_test_data())
  
  async def test_integration_whoami(self):
    client = await create_admin_client()
    response = await client.whoami()
    self.assertTrue(response['account'] == "conjur")
  
  async def test_integration_list(self):
    client = await create_admin_client()
    resources = await client.list()
    self.assertGreater(len(resources), 6)

  async def test_integration_variable(self):
    client = await create_admin_client()
    await client.set('data/foo', 'test-value')
    response = await client.get('data/foo')
    self.assertTrue(response == b'test-value')

  async def test_integration_variable_not_found(self):
    client = await create_admin_client()
    with self.assertRaises(Exception) as context:
      response = await client.get('data/non-existing-variable')
    self.assertEqual(context.exception.status, 404)

  async def test_integration_fetch_multiple_variables(self):
    client = await create_admin_client()
    await client.set('data/foo', 'test-value1')
    await client.set('data/bar', 'test-value2')
    await client.set('data/baz', 'test-value3')

    response = await client.get_many('data/foo', 'data/bar', 'data/baz')
    self.assertEqual(response['data/foo'], 'test-value1')
    self.assertEqual(response['data/bar'], 'test-value2')
    self.assertEqual(response['data/baz'], 'test-value3')

  @classmethod
  async def _add_test_data(cls):
    c = await create_admin_client()
    await c.load_policy_file("data", "tests/integration/policies/common.yml")
