"""
Tests for API client
"""

import unittest
from unittest.mock import Mock, patch
from check_dolphin.api_client import DolphinSchedulerClient


class TestDolphinSchedulerClient(unittest.TestCase):
    """Test DolphinScheduler API client"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = DolphinSchedulerClient(
            base_url="http://localhost:12345/dolphinscheduler",
            token="test-token"
        )

    def test_init(self):
        """Test client initialization"""
        self.assertEqual(self.client.base_url, "http://localhost:12345/dolphinscheduler")
        self.assertEqual(self.client.token, "test-token")
        self.assertEqual(self.client.headers['token'], "test-token")

    @patch('requests.request')
    def test_get_projects_success(self, mock_request):
        """Test get projects with successful response"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'totalList': [
                    {'code': 123, 'name': 'Project 1'},
                    {'code': 456, 'name': 'Project 2'}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        projects = self.client.get_projects()

        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0]['code'], 123)
        self.assertEqual(projects[1]['name'], 'Project 2')


if __name__ == '__main__':
    unittest.main()
