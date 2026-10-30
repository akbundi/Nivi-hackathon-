# AI Reality Reconstructor

<p align="center">
  <strong>Transforming fragmented evidence into a structured, explainable investigation.</strong>
</p>

<p align="center">
  An AI-assisted investigation platform concept for organizing evidence events, identifying timeline gaps, and generating follow-up questions.
</p>

---

## Overview

**AI Reality Reconstructor** is a modular investigation-support project designed to help organize information from multiple evidence sources into a clearer investigation workflow.

The project is intended to bring together evidence records, chronological events, investigation analysis, and scene reconstruction in one platform. Its current working implementation includes a React-based investigation dashboard and a FastAPI service that analyzes evidence events, detects time gaps, checks for missing evidence-source categories, and suggests follow-up questions.

The broader repository is structured to support future modules for evidence ingestion, timeline reasoning, investigation intelligence, and 2D/3D scene visualization.

> **Project status:** The frontend dashboard and the `/analyze` backend workflow are implemented in the current codebase. Several other directories are architectural placeholders for planned functionality and are not yet implemented.

## Key Features

### Implemented

- **Investigation dashboard:** A React interface for reviewing and editing evidence events.
- **Evidence event inputs:** Capture or edit an event's timestamp, source, location, and description.
- **Timeline gap detection:** Identify intervals between consecutive events that exceed the configured threshold.
- **Missing-source checks:** Flag absent source categories such as CCTV, sensor, access, and witness records.
- **Severity classification:** Assign high or medium severity to detected gaps based on the current time-gap rules.
- **Automated follow-up questions:** Generate investigation questions based on the detected gap and its associated evidence sources.
- **Analysis summary:** Display the number of detected gaps, suggested questions, and high-severity gaps.
- **REST API:** Expose the analysis workflow through FastAPI.
- **Health endpoint:** Check whether the backend service is running.

### Planned / Not yet implemented

The repository includes folders for the following capabilities, but the uploaded code does not yet contain working implementations for them:

- Evidence ingestion from documents, images, videos, and sensor data.
- Automated media processing, OCR, and frame extraction.
- Entity linking and evidence-graph construction.
- Advanced temporal reasoning and contradiction detection.
- Evidence confidence scoring and investigation report generation.
- Automated 2D/3D scene reconstruction and spatial positioning.
- Interactive 3D scene navigation, camera controls, and evidence markers.
- Persistent storage, authentication, and end-to-end orchestration.

These capabilities describe the intended project architecture, not currently available features.

## System Architecture

The repository is organized into separate modules so that individual capabilities can be developed independently.

```text
AI-Reality-Reconstructor/
│
├── member_1_frontend/              # React + Vite investigation dashboard
│   └── src/
│       ├── App.jsx                 # Evidence inputs and analysis results
│       └── styles.css              # Dashboard styling
│
├── member_2_evidence/              # Planned evidence-ingestion module
│   ├── document/
│   ├── image/
│   ├── video/
│   ├── sensor/
│   └── processors/
│
├── member_3_timeline/              # Planned timeline and event reasoning
│   ├── entity_linking/
│   ├── event_builder/
│   ├── evidence_graph/
│   └── temporal_reasoning/
│
├── member_4_investigation/         # Planned investigation intelligence
│   ├── contradiction_detection/
│   ├── evidence_scoring/
│   ├── gap_detection/
│   ├── question_generation/
│   └── report_generation/
│
├── member_5_scene/                 # Planned spatial reconstruction
│   ├── positioning/
│   ├── scene_2d/
│   ├── scene_3d/
│   └── spatial_extraction/
│
├── member_6_backend/               # FastAPI investigation API
│   ├── api/
│   │   └── main.py
│   └── requirements.txt
│
├── member_7_3dor3js_visualization/ # Planned 3D / Three.js visualization
│   └── src/
│       ├── camera/
│       ├── floor_plan/
│       ├── interactions/
│       ├── objects/
│       ├── scene/
│       └── timeline/
│
├── shared/                         # Planned shared models and schemas
├── sample_data/                    # Sample-data directory structure
├── mock_outputs/                   # Mock output directory structure
├── real_outputs/                   # Generated-output directory structure
├── tests/                          # Test directory structure
├── .env.example
├── docker-compose.yml
└── README.md
```

*Note: Several listed directories and files are currently empty placeholders. The architecture shows the intended module boundaries.*

## Technology Stack

| Layer | Technology | Current use |
|---|---|---|
| Frontend | React 18 | Investigation dashboard |
| Frontend tooling | Vite 5 | Development server and production build |
| Styling | CSS | Dashboard layout and visual design |
| Backend | Python | Analysis service |
| API framework | FastAPI | REST endpoints |
| Data validation | Pydantic | Request and response models |
| ASGI server | Uvicorn | Local API server |
| API communication | Fetch API / JSON | Frontend-to-backend requests |

## How the Current Workflow Works

```text
User
  |
  v
React Investigation Dashboard
  |
  |  Evidence events (JSON)
  v
FastAPI POST /analyze
  |
  +--> Sort events by timestamp
  |
  +--> Detect time gaps
  |
  +--> Check required evidence sources
  |
  +--> Assign severity
  |
  +--> Generate follow-up questions
  |
  v
JSON Analysis Response
  |
  v
Dashboard Results
  |
  +--> Gap count
  +--> Suggested-question count
  +--> High-severity count
  +--> Detected gaps and questions
```

### Current analysis logic

1. The dashboard starts with sample evidence events that users can edit.
2. When the user runs an investigation analysis, the frontend sends the events to `POST /analyze`.
3. The backend sorts events chronologically.
4. It detects gaps greater than the configured three-minute threshold.
5. It checks whether the configured source categories are represented.
6. It classifies detected gaps as medium or high severity.
7. It generates follow-up questions using the gap's location, time range, and associated sources.
8. The frontend displays the returned analysis.

**Current rule configuration:** The gap threshold is three minutes. A detected time gap is classified as high severity when it exceeds fifteen minutes; otherwise, it is medium. The source check currently expects CCTV, sensor, access, and witness records.

## Getting Started

### Prerequisites

Install the following before running the project:

- Node.js and npm
- Python 3.9 or later
- pip

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd AI-Reality-Reconstructor
```

If the project is already downloaded, open the `AI-Reality-Reconstructor` folder in your terminal.

### 2. Start the backend

Open a terminal:

```bash
cd member_6_backend
python -m venv .venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

### 3. Start the frontend

Open a second terminal from the project root:

```bash
cd member_1_frontend
npm install
npm run dev
```

Open the Vite development URL:

```text
http://localhost:5173
```

The frontend uses `http://localhost:8000` as its default API base URL.

To configure a different backend URL, create a `.env` file inside `member_1_frontend`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Restart the Vite development server after changing environment variables.

## API Reference

### `GET /health`

Checks backend availability.

**Example response:**

```json
{
  "status": "ok"
}
```

### `POST /analyze`

Analyzes a list of evidence events and returns detected gaps and suggested questions.

**Request body:**

```json
{
  "events": [
    {
      "timestamp": "2024-06-20 09:12",
      "source": "CCTV",
      "location": "Corridor B",
      "description": "Person seen in corridor"
    },
    {
      "timestamp": "2024-06-20 09:18",
      "source": "sensor",
      "location": "Main Door",
      "description": "Door access sensor triggered"
    },
    {
      "timestamp": "2024-06-20 09:26",
      "source": "witness",
      "location": "Outside Gate",
      "description": "Witness confirms route near gate"
    }
  ]
}
```

**Response structure:**

```json
{
  "gaps": [
    {
      "start": "2024-06-20 09:12",
      "end": "2024-06-20 09:18",
      "location": "Corridor B",
      "reason": "Missing evidence between consecutive events",
      "sources": ["CCTV", "sensor"],
      "severity": "medium"
    }
  ],
  "questions": [
    "Is there additional CCTV footage or a nearby camera covering Corridor B between 2024-06-20 09:12 and 2024-06-20 09:18?"
  ]
}
```

The example response is illustrative. Actual results depend on the submitted events and the backend's analysis rules. The backend may return additional gaps for missing source categories.

## Configuration

| Variable | Description | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend | `http://localhost:8000` |

The root `.env.example` is currently empty. The frontend environment variable above is the configuration currently read by the application.

## Current Limitations

- The frontend currently uses editable sample events; there is no connected file-upload workflow in the inspected implementation.
- The analysis is rule-based and does not currently use a trained AI/ML model.
- The backend currently analyzes timestamp, source, location, and description fields; it does not process raw media files.
- Evidence, timeline, and investigation results are not persisted in a database.
- The current API uses permissive CORS settings and should be configured more securely before production deployment.
- Automated tests, authentication, and production deployment configuration are not present in the inspected implementation.
- The root `requirements.txt` and `docker-compose.yml` are empty, so the project should currently be started using the separate frontend and backend instructions above.

## Roadmap

- [ ] Implement evidence upload and ingestion for supported file types.
- [ ] Add document text extraction, image analysis, video-frame processing, and sensor-data ingestion.
- [ ] Define and validate shared evidence, timeline, investigation, and scene schemas.
- [ ] Build chronological event linking and evidence-graph generation.
- [ ] Add contradiction detection, evidence scoring, and advanced gap analysis.
- [ ] Generate structured investigation reports.
- [ ] Implement 2D/3D scene reconstruction and spatial evidence mapping.
- [ ] Connect the 3D visualization layer to investigation and timeline data.
- [ ] Add database persistence, authentication, and access control.
- [ ] Add unit, integration, and end-to-end tests.
- [ ] Complete Docker-based setup and deployment configuration.

## Contributing

Contributions are welcome as the project develops.

1. Fork the repository.
2. Create a feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make and test your changes.
4. Commit your work:

   ```bash
   git commit -m "Add: your feature description"
   ```

5. Push your branch and open a pull request.

For larger changes, coordinate with the team so shared schemas and module interfaces remain consistent.

## Team

**Project:** AI Reality Reconstructor  
**Event:** Hackathon project

Add the verified team member names, roles, and profile links here.

## Disclaimer

AI Reality Reconstructor is an investigation-support project. Its outputs are intended to help organize information and identify areas that may need further review. Detected gaps and generated questions are rule-based suggestions, not proof of an event or a determination of responsibility. Any real-world conclusions require independent verification and human judgment.

## License

No license has been specified in the inspected repository. Add a `LICENSE` file and update this section once the project team has selected a license.
