"""
RootCause MOCK backend. Use ONLY to test the frontend when the real backend is not running.
Implements the exact contract in ROOTCAUSE_API_CONTRACT.md on http://127.0.0.1:8000

    pip install -r requirements.txt
    python mock_server.py

Environment switches (for testing):
    MOCK_SPEED=3     run the simulated investigation 3x faster
    MOCK_NO_WS=1     refuse WebSocket connections, to test the polling fallback
"""
import asyncio
import os
import uuid

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SPEED = float(os.getenv("MOCK_SPEED", "1"))
NO_WS = os.getenv("MOCK_NO_WS") == "1"
COLDSTART = float(os.getenv("MOCK_COLDSTART", "0"))
UNKNOWN_REPO = os.getenv("MOCK_UNKNOWN_REPO") == "1"

app = FastAPI(title="RootCause mock backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HYPS = [
    ("race_condition", "Race Condition"),
    ("dependency_bump", "Dependency Version Bump"),
    ("off_by_one", "Off-by-One Error"),
    ("api_contract_break", "Broken API Contract"),
]
CURVES = {
    "race_condition": [9, 17, 26, 34, 41, 48],
    "dependency_bump": [8, 21, 38, 57, 76, 92],
    "off_by_one": [12, 16, 14, 10, 7, 4],
    "api_contract_break": [6, 12, 15, 11, 8, 5],
}
REPORT = {
    "commit_hash": "9d41c07be3a2f5518c6d0e4b7a1f3925ce80b6d4",
    "commit_message": "chore: bump orjson 3.9.15 -> 3.10.0",
    "author": "dev.sample",
    "root_cause_id": "dependency_bump",
    "root_cause_label": "Dependency Version Bump",
    "explanation": (
        "The orjson upgrade changed the default serialization of datetime values, so the API now "
        "returns timestamps in a different format and the test that compares the JSON payload fails."
    ),
    "fix_diff": (
        "diff --git a/api/serializers.py b/api/serializers.py\n"
        "--- a/api/serializers.py\n"
        "+++ b/api/serializers.py\n"
        "@@ -12,7 +12,7 @@ def to_json(payload):\n"
        "-    return orjson.dumps(payload)\n"
        "+    return orjson.dumps(payload, option=orjson.OPT_NAIVE_UTC | orjson.OPT_UTC_Z)"
    ),
    "regression_test": (
        "import json\n"
        "from datetime import datetime, timezone\n"
        "from api.serializers import to_json\n\n"
        "def test_datetime_serialization_is_stable():\n"
        "    out = json.loads(to_json({\"at\": datetime(2026, 1, 1, tzinfo=timezone.utc)}))\n"
        "    assert out[\"at\"] == \"2026-01-01T00:00:00Z\""
    ),
    "summary": (
        "A dependency bump silently changed the default datetime format. Pinning the serializer options "
        "restores the old output, and the new test fails on the old behaviour and passes on the fix."
    ),
}

INV: dict = {}
SUBS: dict = {}


class Req(BaseModel):
    repo_path: str
    failing_test: str
    error_log: str


async def emit(iid: str, msg: dict):
    for ws in list(SUBS.get(iid, ())):
        try:
            await ws.send_json(msg)
        except Exception:
            SUBS[iid].discard(ws)


async def nap(seconds: float):
    await asyncio.sleep(seconds / SPEED)


async def simulate(iid: str, unknown: bool = False):
    st = INV[iid]
    if unknown:
        await nap(1.0)
        st["phase"] = "planning"; await emit(iid, {"type": "phase_change", "phase": "planning"})
        await nap(1.0)
        rep = {
            "commit_hash": "unknown", "commit_message": "Repository not found or is not a git repository",
            "author": "unknown", "root_cause_id": "dependency_bump", "root_cause_label": "Dependency Version Bump",
            "explanation": "The repository could not be bisected.", "fix_diff": "", "regression_test": "",
            "summary": "Repository not found or is not a git repository",
        }
        st["report"] = rep; st["phase"] = "complete"
        await emit(iid, {"type": "phase_change", "phase": "complete"})
        await emit(iid, {"type": "complete", "report": rep})
        return
    total = 12
    st["bisection_progress"]["total_commits"] = total

    async def phase(p):
        st["phase"] = p
        await emit(iid, {"type": "phase_change", "phase": p})

    await nap(1.0)
    await phase("planning")
    await nap(1.5)
    await phase("bisecting")
    for i in range(1, total + 1):
        h = uuid.uuid4().hex + uuid.uuid4().hex[:8]
        st["bisection_progress"].update(current_commit=h, commits_checked=i)
        await emit(iid, {"type": "bisection_update", "commit_hash": h, "commits_checked": i, "total_commits": total})
        await nap(0.35)
    await phase("hypothesis_testing")
    for r in range(6):
        for hid, _ in HYPS:
            c = CURVES[hid][r]
            st["hyps"][hid].update(confidence=c, status="testing")
            await emit(iid, {"type": "hypothesis_update", "id": hid, "confidence": c, "status": "testing"})
            await nap(0.15)
        await nap(0.5)
    st["hyps"]["dependency_bump"].update(confidence=94, status="confirmed")
    await emit(iid, {"type": "hypothesis_update", "id": "dependency_bump", "confidence": 94, "status": "confirmed"})
    for hid, _ in HYPS:
        if hid != "dependency_bump":
            st["hyps"][hid]["status"] = "ruled_out"
            await emit(iid, {"type": "hypothesis_update", "id": hid,
                             "confidence": st["hyps"][hid]["confidence"], "status": "ruled_out"})
            await nap(0.3)
    await nap(1.0)
    await phase("fixing")
    await nap(2.0)
    st["report"] = REPORT
    st["phase"] = "complete"
    await emit(iid, {"type": "complete", "report": REPORT})


@app.post("/api/investigate")
async def investigate(req: Req):
    if COLDSTART > 0:
        await asyncio.sleep(COLDSTART)
    iid = str(uuid.uuid4())
    INV[iid] = {
        "investigation_id": iid,
        "phase": "planning",
        "bisection_progress": {"current_commit": "", "commits_checked": 0, "total_commits": 0},
        "hyps": {hid: {"id": hid, "label": lbl, "confidence": 0, "status": "testing"} for hid, lbl in HYPS},
        "report": None,
    }
    SUBS[iid] = set()
    asyncio.create_task(simulate(iid, unknown=UNKNOWN_REPO))
    return {"investigation_id": iid, "status": "started"}


@app.get("/api/investigation/{iid}/status")
async def status(iid: str):
    st = INV.get(iid)
    if not st:
        raise HTTPException(404, "unknown investigation")
    return {
        "investigation_id": iid,
        "phase": st["phase"],
        "bisection_progress": st["bisection_progress"],
        "hypotheses": [st["hyps"][h] for h, _ in HYPS],
    }


@app.get("/api/investigation/{iid}/report")
async def report(iid: str):
    st = INV.get(iid)
    if not st:
        raise HTTPException(404, "unknown investigation")
    if not st["report"]:
        raise HTTPException(409, "investigation not complete")
    return st["report"]


@app.websocket("/ws/investigation/{iid}")
async def ws_endpoint(ws: WebSocket, iid: str):
    if NO_WS or iid not in INV:
        await ws.close(code=1008)
        return
    await ws.accept()
    SUBS[iid].add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        SUBS[iid].discard(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
