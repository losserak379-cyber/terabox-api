import os
import re
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI(title="TeraBox API Gateway", version="0.1.0")

# Configure a compatible, trusted extraction provider here.
# The provider must be authorized to resolve public/shared TeraBox links.
EXTRACTOR_API_URL = os.getenv("EXTRACTOR_API_URL", "").strip()
EXTRACTOR_API_KEY = os.getenv("EXTRACTOR_API_KEY", "").strip()
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "25"))

TERABOX_HOSTS = {
    "terabox.com", "www.terabox.com", "1024terabox.com",
    "www.1024terabox.com", "teraboxapp.com", "www.teraboxapp.com",
    "terabox.app", "www.terabox.app", "teraboxlink.com",
    "www.teraboxlink.com",
}

class ExtractRequest(BaseModel):
    url: HttpUrl

def validate_terabox_url(url: str) -> str:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in TERABOX_HOSTS:
        raise HTTPException(status_code=400, detail="Please send a supported HTTPS TeraBox share link.")
    return url

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "extractor_configured": str(bool(EXTRACTOR_API_URL)).lower()}

@app.post("/extract")
async def extract_link(payload: ExtractRequest) -> dict[str, Any]:
    url = validate_terabox_url(str(payload.url))
    if not EXTRACTOR_API_URL:
        raise HTTPException(
            status_code=503,
            detail="No extraction provider configured. Set EXTRACTOR_API_URL to a trusted, compatible provider."
        )

    headers = {"Accept": "application/json"}
    if EXTRACTOR_API_KEY:
        headers["Authorization"] = f"Bearer {EXTRACTOR_API_KEY}"

    # Provider-specific request/response formats vary. This gateway expects:
    # POST JSON {"url": "..."} -> JSON {"download_url": "...", "filename": "...", "size": 123}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=False) as client:
            response = await client.post(EXTRACTOR_API_URL, json={"url": url}, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Extraction provider timed out.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Extraction provider request failed or returned invalid JSON.") from exc

    download_url = data.get("download_url")
    if not isinstance(download_url, str) or not download_url.startswith("https://"):
        raise HTTPException(status_code=502, detail="Provider response must contain an HTTPS download_url.")
    return {
        "filename": str(data.get("filename") or "video.mp4")[:200],
        "size": data.get("size"),
        "download_url": download_url,
    }
