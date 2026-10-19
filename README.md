# TeraBox API Gateway

A small FastAPI gateway for a compatible, trusted TeraBox extraction provider.

## Endpoints
- `GET /health` — health check
- `POST /extract` — accepts `{"url":"https://..."}` and expects provider JSON with `download_url`, optionally `filename` and `size`.

## Configure
Set `EXTRACTOR_API_URL` to the provider endpoint and optionally `EXTRACTOR_API_KEY` in Railway Variables.

**This project does not itself extract TeraBox links.** Extraction services use different APIs and response formats; adapt `main.py` to the provider's published documentation before production use. Do not use private account credentials or bypass access controls. Only process links you are authorized to access.

## Run locally
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
