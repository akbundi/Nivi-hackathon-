# AI Reality Reconstructor Frontend

This frontend provides a simple investigation dashboard that sends evidence events to the backend and displays detected gaps and follow-up questions.

## Run locally

```bash
cd AI-Reality-Reconstructor/member_1_frontend
npm install
npm run dev
```

Then open the local Vite URL, usually:

```text
http://localhost:5173/
```

## Backend connection

The app expects the Python API to be running on:

```text
http://localhost:8000
```

If needed, set the environment variable:

```bash
VITE_API_BASE_URL=http://localhost:8000
```
