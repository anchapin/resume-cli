import pytest
import socket
from unittest.mock import patch, Mock
from cli.integrations.job_parser import JobParser


class TestSSRFProtection:
    """Test SSRF protection in JobParser."""

    def setup_method(self):
        self.parser = JobParser()
        # Mock cache to prevent cache hits and writes affecting tests
        self.parser._get_from_cache = Mock(return_value=None)
        self.parser._save_to_cache = Mock()

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1",
            "http://localhost",
            "http://10.0.0.1",
            "http://192.168.1.1",
            "http://172.16.0.1",
            "http://[::1]",
            "ftp://example.com",  # Invalid scheme
            "file:///etc/passwd",  # Invalid scheme
        ],
    )
    def test_parse_from_url_blocks_restricted_access(self, url):
        """Verify that parse_from_url raises RuntimeError (wrapping ValueError) for restricted URLs."""
        # Mock requests.Session to ensure we don't actually make requests
        with patch("requests.Session") as MockSession:
            session_instance = MockSession.return_value
            # Ensure the context manager returns the session instance
            session_instance.__enter__.return_value = session_instance

            # We expect a RuntimeError due to SSRF protection
            with pytest.raises(RuntimeError, match="Security validation failed|restricted|scheme"):
                self.parser.parse_from_url(url)

            # Verify session.get was NOT called
            session_instance.get.assert_not_called()

    def test_parse_from_url_allows_public_access(self):
        """Verify that parse_from_url allows public URLs."""
        url = "http://example.com"

        # Mock requests.Session
        with patch("requests.Session") as MockSession:
            session_instance = MockSession.return_value
            session_instance.__enter__.return_value = session_instance

            mock_response = Mock()
            mock_response.text = "<html><body><h1>Job Title</h1></body></html>"
            mock_response.status_code = 200
            mock_response.is_redirect = False
            mock_response.url = url
            session_instance.get.return_value = mock_response

            # Mock socket.getaddrinfo to resolve to a public IP
            public_ip = "93.184.216.34"
            mock_addr_info = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (public_ip, 80))]

            with patch("socket.getaddrinfo", return_value=mock_addr_info):
                self.parser.parse_from_url(url)

            # Verify session.get WAS called
            session_instance.get.assert_called()

    def test_parse_from_url_blocks_redirect_to_private(self):
        """Verify that redirect to private IP is blocked."""
        url = "http://example.com/redirect"
        target_url = "http://127.0.0.1/admin"

        # Mock requests.Session
        with patch("requests.Session") as MockSession:
            session_instance = MockSession.return_value
            session_instance.__enter__.return_value = session_instance

            # First response: 302 Redirect
            resp1 = Mock()
            resp1.is_redirect = True
            resp1.headers = {"Location": target_url}
            resp1.status_code = 302
            resp1.url = url  # important for urljoin

            # Second response (should not be reached if validation works)
            resp2 = Mock()
            resp2.is_redirect = False
            resp2.status_code = 200

            session_instance.get.side_effect = [resp1, resp2]

            # Mock socket.getaddrinfo
            def getaddrinfo_side_effect(host, port, family=0, type=0, proto=0, flags=0):
                # Check if host is 127.0.0.1 (from target_url)
                if host == "127.0.0.1":
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]
                # Default to public IP
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]

            with patch("socket.getaddrinfo", side_effect=getaddrinfo_side_effect):
                # We expect RuntimeError when following redirect to private IP
                with pytest.raises(RuntimeError, match="Security validation failed|restricted"):
                    self.parser.parse_from_url(url)
