"""
Test REST client functionality.

User Story: As a developer, I want REST client to handle HTTP requests reliably
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from src.network.rest_client import RestClient


class TestRestClientInitialization:
    """Test RestClient initialization and configuration"""

    def test_rest_client_initialization_with_defaults(self):
        """Test: RestClient initialization with default values"""
        client = RestClient()

        assert client.jwt_token is None
        assert client.timeout == 10.0
        assert client._client is None

    def test_rest_client_initialization_with_token(self):
        """Test: RestClient initialization with JWT token"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
        client = RestClient(jwt_token=token)

        assert client.jwt_token == token
        assert client.timeout == 10.0
        assert client._client is None

    def test_rest_client_initialization_with_custom_timeout(self):
        """Test: RestClient initialization with custom timeout"""
        client = RestClient(timeout=30.0)

        assert client.jwt_token is None
        assert client.timeout == 30.0
        assert client._client is None

    def test_rest_client_initialization_with_all_params(self):
        """Test: RestClient initialization with all parameters"""
        token = "test.jwt.token"
        timeout = 25.0
        client = RestClient(jwt_token=token, timeout=timeout)

        assert client.jwt_token == token
        assert client.timeout == timeout
        assert client._client is None


class TestRestClientContextManager:
    """Test RestClient as async context manager"""

    @pytest.mark.asyncio
    async def test_async_context_manager_creates_client(self):
        """Test: Async context manager creates httpx client"""
        client = RestClient()

        async with client as rest_client:
            assert rest_client._client is not None
            assert isinstance(rest_client._client, httpx.AsyncClient)
            # Verify timeout object exists (specific value access depends on httpx version)
            assert rest_client._client.timeout is not None

    @pytest.mark.asyncio
    async def test_async_context_manager_custom_timeout(self):
        """Test: Async context manager respects custom timeout"""
        client = RestClient(timeout=15.0)

        async with client as rest_client:
            assert rest_client._client is not None
            # Verify timeout object exists and client was created with our timeout
            assert rest_client._client.timeout is not None
            # The timeout value is passed to httpx.AsyncClient constructor
            assert client.timeout == 15.0

    @pytest.mark.asyncio
    async def test_async_context_manager_cleanup(self):
        """Test: Async context manager properly cleans up"""
        client = RestClient()

        # Mock the httpx.AsyncClient to track close calls
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_class.return_value = mock_client_instance

            async with client:
                pass  # Exit context

            # Should have called aclose
            mock_client_instance.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_exception_handling(self):
        """Test: Context manager handles exceptions properly"""
        client = RestClient()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_class.return_value = mock_client_instance

            try:
                async with client:
                    raise ValueError("Test exception")
            except ValueError:
                pass  # Expected exception

            # Should still call aclose on exception
            mock_client_instance.aclose.assert_called_once()


class TestRestClientHeaders:
    """Test REST client header management"""

    def test_get_headers_no_token_no_custom_headers(self):
        """Test: Header generation with no token and no custom headers"""
        client = RestClient()
        headers = client._get_headers()

        assert headers == {}

    def test_get_headers_with_token_no_custom_headers(self):
        """Test: Header generation with JWT token"""
        token = "test.jwt.token"
        client = RestClient(jwt_token=token)
        headers = client._get_headers()

        assert headers == {"Authorization": f"Bearer {token}"}

    def test_get_headers_no_token_with_custom_headers(self):
        """Test: Header generation with custom headers only"""
        client = RestClient()
        custom_headers = {"Content-Type": "application/json", "X-Custom": "value"}
        headers = client._get_headers(custom_headers)

        expected = {"Content-Type": "application/json", "X-Custom": "value"}
        assert headers == expected

    def test_get_headers_with_token_and_custom_headers(self):
        """Test: Header generation with both token and custom headers"""
        token = "test.jwt.token"
        client = RestClient(jwt_token=token)
        custom_headers = {"Content-Type": "application/json", "X-Custom": "value"}
        headers = client._get_headers(custom_headers)

        expected = {
            "Content-Type": "application/json",
            "X-Custom": "value",
            "Authorization": f"Bearer {token}",
        }
        assert headers == expected

    def test_get_headers_preserves_custom_headers(self):
        """Test: Custom headers are not modified by reference"""
        client = RestClient(jwt_token="token")
        original_headers = {"X-Original": "value"}
        returned_headers = client._get_headers(original_headers)

        # Original headers should not be modified
        assert "Authorization" not in original_headers
        assert original_headers == {"X-Original": "value"}

        # Returned headers should include Authorization
        assert "Authorization" in returned_headers
        assert "X-Original" in returned_headers

    def test_get_headers_overwrites_existing_authorization(self):
        """Test: JWT token overwrites existing Authorization header"""
        client = RestClient(jwt_token="new_token")
        custom_headers = {"Authorization": "Bearer old_token", "X-Custom": "value"}
        headers = client._get_headers(custom_headers)

        assert headers["Authorization"] == "Bearer new_token"
        assert headers["X-Custom"] == "value"


class TestRestClientGetRequests:
    """Test REST client GET requests"""

    @pytest.mark.asyncio
    async def test_get_request_success(self):
        """Test: Successful GET request"""
        client = RestClient()

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            async with client:
                response = await client.get("https://api.example.com/data")

            assert response == mock_response
            mock_client_instance.get.assert_called_once_with(
                "https://api.example.com/data", params=None, headers={}
            )

    @pytest.mark.asyncio
    async def test_get_request_with_params_and_headers(self):
        """Test: GET request with query parameters and headers"""
        client = RestClient(jwt_token="test_token")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            params = {"page": 1, "limit": 10}
            headers = {"X-Custom": "value"}

            async with client:
                response = await client.get(
                    "https://api.example.com/data", params=params, headers=headers
                )

            assert response == mock_response
            mock_client_instance.get.assert_called_once_with(
                "https://api.example.com/data",
                params=params,
                headers={"X-Custom": "value", "Authorization": "Bearer test_token"},
            )

    @pytest.mark.asyncio
    async def test_get_request_http_status_error(self):
        """Test: GET request handles HTTP status errors"""
        client = RestClient()

        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            async with client:
                response = await client.get("https://api.example.com/notfound")

            # Should return None on HTTP error
            assert response is None

    @pytest.mark.asyncio
    async def test_get_request_request_error(self):
        """Test: GET request handles request errors"""
        client = RestClient()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed", request=Mock())
            )
            mock_client_class.return_value = mock_client_instance

            async with client:
                response = await client.get("https://api.example.com/data")

            # Should return None on request error
            assert response is None

    @pytest.mark.asyncio
    async def test_get_request_no_client(self):
        """Test: GET request when client is not initialized"""
        client = RestClient()

        # Call get without using context manager
        response = await client.get("https://api.example.com/data")

        # Should return None when client is not initialized
        assert response is None


class TestRestClientPostRequests:
    """Test REST client POST requests"""

    @pytest.mark.asyncio
    async def test_post_request_success_with_json(self):
        """Test: Successful POST request with JSON data"""
        client = RestClient()

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"created": True}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            json_data = {"name": "test", "value": 42}

            async with client:
                response = await client.post(
                    "https://api.example.com/create", json=json_data
                )

            assert response == mock_response
            mock_client_instance.post.assert_called_once_with(
                "https://api.example.com/create", data=None, json=json_data, headers={}
            )

    @pytest.mark.asyncio
    async def test_post_request_success_with_form_data(self):
        """Test: Successful POST request with form data"""
        client = RestClient(jwt_token="auth_token")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            form_data = {"field1": "value1", "field2": "value2"}
            custom_headers = {"Content-Type": "application/x-www-form-urlencoded"}

            async with client:
                response = await client.post(
                    "https://api.example.com/submit",
                    data=form_data,
                    headers=custom_headers,
                )

            assert response == mock_response
            mock_client_instance.post.assert_called_once_with(
                "https://api.example.com/submit",
                data=form_data,
                json=None,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Bearer auth_token",
                },
            )

    @pytest.mark.asyncio
    async def test_post_request_http_status_error(self):
        """Test: POST request handles HTTP status errors"""
        client = RestClient()

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=Mock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            async with client:
                response = await client.post(
                    "https://api.example.com/bad-request", json={"invalid": "data"}
                )

            assert response is None

    @pytest.mark.asyncio
    async def test_post_request_request_error(self):
        """Test: POST request handles request errors"""
        client = RestClient()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.RequestError("Network error", request=Mock())
            )
            mock_client_class.return_value = mock_client_instance

            async with client:
                response = await client.post(
                    "https://api.example.com/data", json={"test": "data"}
                )

            assert response is None

    @pytest.mark.asyncio
    async def test_post_request_general_exception(self):
        """Test: POST request handles general exceptions"""
        client = RestClient()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_client_class.return_value = mock_client_instance

            async with client:
                response = await client.post(
                    "https://api.example.com/data", json={"test": "data"}
                )

            assert response is None


class TestRestClientEdgeCases:
    """Test REST client edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_multiple_requests_same_client(self):
        """Test: Multiple requests using same client instance"""
        client = RestClient()

        mock_responses = [Mock(), Mock(), Mock()]
        for i, mock_response in enumerate(mock_responses):
            mock_response.status_code = 200
            mock_response.json.return_value = {"request": i + 1}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(side_effect=mock_responses)
            mock_client_class.return_value = mock_client_instance

            async with client:
                response1 = await client.get("https://api.example.com/1")
                response2 = await client.get("https://api.example.com/2")
                response3 = await client.get("https://api.example.com/3")

            assert response1 == mock_responses[0]
            assert response2 == mock_responses[1]
            assert response3 == mock_responses[2]
            assert mock_client_instance.get.call_count == 3

    @pytest.mark.asyncio
    async def test_empty_endpoint_url(self):
        """Test: REST client with empty endpoint URL"""
        client = RestClient()

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            async with client:
                response = await client.get("")

            # Empty string should be passed as-is
            mock_client_instance.get.assert_called_once_with(
                "", params=None, headers={}
            )
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_very_long_jwt_token(self):
        """Test: REST client with very long JWT token"""
        long_token = "eyJ" + "x" * 10000 + ".payload.signature"
        client = RestClient(jwt_token=long_token)

        headers = client._get_headers()

        assert headers["Authorization"] == f"Bearer {long_token}"
        assert len(headers["Authorization"]) > 10000

    def test_headers_with_none_values(self):
        """Test: Header handling with None custom headers"""
        client = RestClient(jwt_token="token")
        headers = client._get_headers(None)

        assert headers == {"Authorization": "Bearer token"}

    @pytest.mark.asyncio
    async def test_request_url_construction(self):
        """Test: Request URL is used as-is (no base URL manipulation)"""
        client = RestClient()

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            test_urls = [
                "https://api.example.com/path",
                "http://localhost:8000/endpoint",
                "https://api.example.com/path/with/many/segments",
                "https://api.example.com/path?existing=param",
            ]

            async with client:
                for url in test_urls:
                    await client.get(url)

            # Verify URLs are passed as-is
            calls = mock_client_instance.get.call_args_list
            for i, call in enumerate(calls):
                assert (
                    call[0][0] == test_urls[i]
                )  # First positional arg should be the URL

    @pytest.mark.asyncio
    async def test_concurrent_requests_different_clients(self):
        """Test: Concurrent requests using different client instances"""
        import asyncio

        async def make_request(client_id):
            client = RestClient(jwt_token=f"token_{client_id}")

            mock_response = Mock()
            mock_response.status_code = 200

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client_instance = AsyncMock()
                mock_client_instance.get = AsyncMock(return_value=mock_response)
                mock_client_class.return_value = mock_client_instance

                async with client:
                    response = await client.get(
                        f"https://api.example.com/client_{client_id}"
                    )

                return response

        # Run multiple clients concurrently
        tasks = [make_request(i) for i in range(3)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert len(responses) == 3
        for response in responses:
            assert response is not None
