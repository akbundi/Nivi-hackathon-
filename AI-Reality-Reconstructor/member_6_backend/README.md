# AI Investigation Layer

This backend module provides the "Gap Detection" and "Smart Question Generation" logic for the AI Reality Reconstructor project.

## Features
- Detects missing time periods between evidence events
- Identifies missing evidence sources like CCTV, access logs, or witnesses
- Generates investigation questions based on detected gaps
- Exposes the logic through a FastAPI endpoint

## Run locally

```bash
cd AI-Reality-Reconstructor/member_6_backend
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Example request

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"timestamp":"2024-06-20 09:12","source":"CCTV","location":"Corridor B","description":"Person seen in corridor"},
      {"timestamp":"2024-06-20 09:14","source":"access","location":"Main Door","description":"Door access sensor activated"},
      {"timestamp":"2024-06-20 09:16","source":"witness","location":"Near Door","description":"Witness saw someone near the entrance"}
    ]
  }'
```
