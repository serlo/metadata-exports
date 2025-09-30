import unittest
from unittest.mock import patch, MagicMock, call

from serlo_api_client import execute


class TestExecuteRetry(unittest.TestCase):
    """Tests for the retry logic in the execute function"""

    @patch("serlo_api_client.Client")
    def test_successful_first_attempt(self, mock_client):
        """Test that execute returns successfully on first attempt"""
        # Setup
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        expected_result = {"data": "test"}
        mock_client_instance.execute.return_value = expected_result

        # Execute
        result = execute("query { test }", {"param": "value"})

        # Assert
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_client_instance.execute.call_count, 1)

    @patch("serlo_api_client.time.sleep")
    @patch("serlo_api_client.Client")
    def test_retry_on_failure_then_success(self, mock_client, mock_sleep):
        """Test that execute retries on failure and eventually succeeds"""
        # Setup
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        expected_result = {"data": "test"}

        # First two calls fail, third succeeds
        mock_client_instance.execute.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            expected_result,
        ]

        # Execute
        result = execute("query { test }")

        # Assert
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_client_instance.execute.call_count, 3)
        # Check sleep was called with exponential backoff: 1s, 2s
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_has_calls([call(1), call(2)])

    @patch("serlo_api_client.time.sleep")
    @patch("serlo_api_client.Client")
    def test_exhausted_retries_raises_exception(self, mock_client, mock_sleep):
        """Test that execute raises the last exception after exhausting retries"""
        # Setup
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        test_exception = Exception("Persistent network error")

        # All calls fail
        mock_client_instance.execute.side_effect = [
            Exception("Network error 1"),
            Exception("Network error 2"),
            test_exception,
        ]

        # Execute and Assert
        with self.assertRaises(Exception) as context:
            execute("query { test }")

        self.assertEqual(str(context.exception), "Persistent network error")
        self.assertEqual(mock_client_instance.execute.call_count, 3)
        # Check sleep was called with exponential backoff: 1s, 2s (not 4s as we fail on 3rd attempt)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_has_calls([call(1), call(2)])

    @patch("serlo_api_client.time.sleep")
    @patch("serlo_api_client.Client")
    def test_retry_with_correct_backoff_times(self, mock_client, mock_sleep):
        """Test that sleep times follow exponential backoff pattern"""
        # Setup
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Fail first attempt, succeed on second
        mock_client_instance.execute.side_effect = [
            Exception("Network error"),
            {"data": "success"},
        ]

        # Execute
        execute("query { test }")

        # Assert - should sleep 1 second (2^0) after first failure
        mock_sleep.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
