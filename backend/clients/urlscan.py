from urllib.parse import urlparse, unquote_plus

import httpx
from starlette.datastructures import Secret

from backend import schemas


class UrlScan(httpx.AsyncClient):
    def __init__(self, api_key: Secret) -> None:
        super().__init__(
            base_url="https://urlscan.io", headers={"api-key": str(api_key)}
        )

    async def lookup(
        self,
        url: str,
    ) -> schemas.UrlScanLookup:
        # Extract the actual URL if it's embedded after &url=
        actual_url = self.extract_embedded_url(url)
        if actual_url:
            url = actual_url
            
        parsed = urlparse(url)
        params = {
            "q": f'task.url:"{url}" AND task.domain:"{parsed.hostname}" AND verdicts.malicious:true',
            "size": 1,
        }
        r = await self.get("/api/v1/search/", params=params)
        r.raise_for_status()
        return schemas.UrlScanLookup.model_validate(r.json())
    
    @staticmethod
    def extract_embedded_url(url_string: str) -> str:
        """
        Extract and decode the actual URL from a string that contains it after &url= parameter.
        
        Example:
        Input: https://example.com/redirect/?param=value&url=https%3a%2f%2factual-site.com
        Output: https://actual-site.com
        
        Returns the extracted URL if found, otherwise returns the original string.
        """
        if "&url=" in url_string:
            parts = url_string.split("&url=", 1)
            if len(parts) > 1 and parts[1]:
                # URL decode the extracted part
                return unquote_plus(parts[1])
        return url_string
