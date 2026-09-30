# RootCause API Contract (Step A input for Bob "document understanding")

Single source of truth for frontend and backend. Do not rename a field.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | /api/investigate | Start a new investigation |
| GET | /api/investigation/{id}/status | Poll current phase + hypothesis confidences |
| WS | /ws/investigation/{id} | Live stream of hypothesis, bisection, and completion events |
| GET | /api/investigation/{id}/report | Final root-cause report |

## POST /api/investigate
Request:
```json
{ "repo_path": "string", "failing_test": "string", "error_log": "string" }
```
Response:
```json
{ "investigation_id": "string (uuid)", "status": "started" }
```

## GET /api/investigation/{id}/status
```json
{
  "investigation_id": "string",
  "phase": "planning | bisecting | hypothesis_testing | fixing | complete",
  "bisection_progress": { "current_commit": "string", "commits_checked": 0, "total_commits": 0 },
  "hypotheses": [
    { "id": "race_condition",     "label": "Race Condition",          "confidence": 0, "status": "testing" },
    { "id": "dependency_bump",    "label": "Dependency Version Bump", "confidence": 0, "status": "testing" },
    { "id": "off_by_one",         "label": "Off-by-One Error",        "confidence": 0, "status": "testing" },
    { "id": "api_contract_break", "label": "Broken API Contract",     "confidence": 0, "status": "testing" }
  ]
}
```
status values: `testing` | `confirmed` | `ruled_out`

## WS /ws/investigation/{id}
One JSON object per message, routed by `type`:
```json
{ "type": "phase_change",      "phase": "..." }
{ "type": "hypothesis_update", "id": "...", "confidence": 0, "status": "..." }
{ "type": "bisection_update",  "commit_hash": "...", "commits_checked": 0, "total_commits": 0 }
{ "type": "complete",          "report": { } }
```

## GET /api/investigation/{id}/report
```json
{
  "commit_hash": "string", "commit_message": "string", "author": "string",
  "root_cause_id": "one of the 4 hypothesis ids", "root_cause_label": "string",
  "explanation": "string", "fix_diff": "string", "regression_test": "string", "summary": "string"
}
```

## Connection defaults
- Backend http://127.0.0.1:8000, frontend http://127.0.0.1:5500
- Backend must enable CORS for the frontend origin
- Use 127.0.0.1 everywhere, never mix with localhost
