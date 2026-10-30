from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="AI Reality Reconstructor - Investigation Layer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvidenceEvent(BaseModel):
    timestamp: str = Field(..., example="2024-06-20 09:12")
    source: str = Field(..., example="CCTV")
    location: str = Field(..., example="Corridor B")
    description: str = Field(..., example="Person seen in corridor")


class AnalyzeRequest(BaseModel):
    events: List[EvidenceEvent]


class GapResult(BaseModel):
    start: str
    end: str
    location: str
    reason: str
    sources: List[str]
    severity: str


class AnalyzeResponse(BaseModel):
    gaps: List[GapResult]
    questions: List[str]


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def detect_gaps(events: List[EvidenceEvent], expected_gap_minutes: int = 3) -> List[Dict[str, Any]]:
    sorted_events = sorted(events, key=lambda e: parse_time(e.timestamp))
    gaps: List[Dict[str, Any]] = []

    for i in range(len(sorted_events) - 1):
        current = sorted_events[i]
        nxt = sorted_events[i + 1]

        current_time = parse_time(current.timestamp)
        next_time = parse_time(nxt.timestamp)
        delta = next_time - current_time

        if delta > timedelta(minutes=expected_gap_minutes):
            gaps.append(
                {
                    "start": current.timestamp,
                    "end": nxt.timestamp,
                    "location": current.location,
                    "reason": "Missing evidence between consecutive events",
                    "sources": [current.source, nxt.source],
                    "severity": "high" if delta > timedelta(minutes=15) else "medium",
                }
            )

    return gaps


def check_missing_sources(events: List[EvidenceEvent], required_sources: List[str]) -> List[Dict[str, Any]]:
    if not events:
        return []

    present_sources = {event.source.lower() for event in events}
    missing = [source for source in required_sources if source.lower() not in present_sources]

    min_time = min(parse_time(event.timestamp) for event in events)
    max_time = max(parse_time(event.timestamp) for event in events)

    gaps: List[Dict[str, Any]] = []
    for source in missing:
        gaps.append(
            {
                "start": min_time.strftime("%Y-%m-%d %H:%M"),
                "end": max_time.strftime("%Y-%m-%d %H:%M"),
                "location": "Investigation-wide",
                "reason": f"Missing {source} records during the critical investigation window",
                "sources": [source],
                "severity": "high",
            }
        )

    return gaps


def generate_question(gap: Dict[str, Any]) -> str:
    sources = [source.lower() for source in gap["sources"]]

    if "cctv" in sources or "video" in sources:
        return (
            f"Is there additional CCTV footage or a nearby camera covering {gap['location']} "
            f"between {gap['start']} and {gap['end']}?"
        )

    if "sensor" in sources or "access" in sources:
        return (
            f"Is there a sensor or access log for {gap['location']} during this period "
            f"from {gap['start']} to {gap['end']}?"
        )

    if "witness" in sources:
        return (
            f"Can another witness or person present at {gap['location']} provide more details "
            f"about the period from {gap['start']} to {gap['end']}?"
        )

    return (
        f"What additional evidence can confirm what happened at {gap['location']} "
        f"between {gap['start']} and {gap['end']}?"
    )


def analyze_events(events: List[EvidenceEvent]) -> Dict[str, List]:
    timeline_gaps = detect_gaps(events)
    source_gaps = check_missing_sources(events, ["CCTV", "sensor", "access", "witness"])
    all_gaps = timeline_gaps + source_gaps
    questions = [generate_question(gap) for gap in all_gaps]

    return {"gaps": all_gaps, "questions": questions}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    result = analyze_events(request.events)
    return {
        "gaps": [
            GapResult(
                start=g["start"],
                end=g["end"],
                location=g["location"],
                reason=g["reason"],
                sources=g["sources"],
                severity=g["severity"],
            )
            for g in result["gaps"]
        ],
        "questions": result["questions"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
