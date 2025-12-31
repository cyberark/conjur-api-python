import pytest
from aiounittest import AsyncTestCase

from tests.integration.integ_utils import create_admin_client


@pytest.mark.integration
class TestIntegrationServerVersion(AsyncTestCase):
    '''
    Integration tests for server version retrieval in Conjur OSS.
    These tests verify that server_version() works correctly and caches the result.
    '''

    async def test_integration_server_version_oss(self):
        """Test that server_version retrieves version from OSS root endpoint"""
        client = await create_admin_client()
        
        # First call should retrieve version from root endpoint
        version = await client.server_version()
        
        # Should return a valid version string (semver format)
        self.assertIsNotNone(version)
        self.assertIsInstance(version, str)
        # Version should be in semver format (e.g., "1.21.1" or "1.24.0-1049")
        self.assertRegex(version, r'^\d+\.\d+\.\d+(?:-\d+)?')
        
        # Verify it's cached
        self.assertIsNotNone(client.conjur_version)
        self.assertEqual(client.conjur_version, version)

    async def test_integration_server_version_caching(self):
        """Test that server_version caches the result and returns same value on subsequent calls"""
        client = await create_admin_client()
        
        # First call
        version1 = await client.server_version()
        self.assertIsNotNone(version1)
        
        # Second call should return cached value
        version2 = await client.server_version()
        self.assertEqual(version1, version2)
        
        # Third call should also return cached value
        version3 = await client.server_version()
        self.assertEqual(version1, version3)
        
        # Verify cache attribute is set
        self.assertEqual(client.conjur_version, version1)

