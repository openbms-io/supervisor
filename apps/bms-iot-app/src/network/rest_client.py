import httpx
from typing import Optional, Dict, Any, Union


class RestClient:
    def __init__(self, jwt_token: Optional[str] = None, timeout: float = 10.0):
        # self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.aclose()

    def _get_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = headers.copy() if headers else {}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        return headers

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[httpx.Response, None]:
        # url = f"{self.base_url}/{endpoint.lstrip('/')}"
        url = endpoint
        if self._client is not None:
            try:
                response = await self._client.get(
                    url, params=params, headers=self._get_headers(headers)
                )
                response.raise_for_status()
                return response
            except httpx.RequestError as exc:
                print(f"An error occurred while requesting {exc.request.url!r}: {exc}")
            except httpx.HTTPStatusError as exc:
                print(
                    f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc}"
                )
        return None

    async def post(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[httpx.Response, None]:
        # url = f"{self.base_url}/{endpoint.lstrip('/')}"
        url = endpoint
        if self._client is not None:
            try:
                response = await self._client.post(
                    url, data=data, json=json, headers=self._get_headers(headers)
                )
                response.raise_for_status()
                return response
            except httpx.RequestError as exc:
                print(f"An error occurred while requesting {exc.request.url!r}: {exc}")
            except httpx.HTTPStatusError as exc:
                print(
                    f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc}"
                )
            except Exception as e:
                print(f"An error occurred while requesting {url!r}: {e}")
        return None
