# RootCause frontend

IBM Bob 2.0 Hackathon · Team CryptiX. Single-file HTML + CSS + vanilla JS. No build step, no npm, no framework.

**This build is already pointed at the deployed backend:** `https://ibm-bob-backend.onrender.com`
You do not need to run a local backend. You do still need to serve this frontend folder yourself (see below) —
the backend's CORS only allows requests from `http://127.0.0.1:5500`.

## Run it (1 command)

```
python -m http.server 5500 --bind 127.0.0.1
```
or double-click `start.bat` (Windows) / run `./start.sh` (Mac/Linux). Then open **http://127.0.0.1:5500** —
not `localhost`, not any other port, not the file directly. The backend will reject anything else.

## First thing to do: click "Test backend connection"

On the page, under "New investigation," click **Test backend connection**. It checks three things against the
real Render backend and reports each separately:

- **Server reachable** — did anything answer at all. Render's free tier sleeps after inactivity, so the first
  check can take 20–50 seconds while it wakes up. This is normal.
- **CORS allows this page** — did the browser let the request through. If this fails but "Server reachable"
  passed, you are not on `http://127.0.0.1:5500`.
- **WebSocket reachable** — did the live-update channel respond.

If all three are green, click **Sample input** then **Open investigation** and you're running the real demo.

## Known thing I could not verify myself

I built this without network access to `ibm-bob-backend.onrender.com` (it's outside my sandbox's allowed
domains), so I read the backend's public source instead of testing it live. Two things follow from that:

1. **The demo repo path.** The backend's own demo script creates a sample repo at `/tmp/rootcause-demo-repo`
   with a failing test at `tests/test_api.py` — the "Sample input" button is pre-filled with exactly this.
   But there's no Procfile or render.yaml in the repo, so I can't confirm Render actually runs that setup
   script before starting the server. **If "Open investigation" comes back with "repository not found,"
   that's the reason — ask your backend teammate whether the Render Start Command runs the demo-repo setup
   before `uvicorn`.** The frontend detects this case and shows a clear banner rather than a fake result.
2. **Everything else** (field names, phases, WebSocket events, report shape) I confirmed by reading
   `main.py` and `models.py` directly — they match `ROOTCAUSE_API_CONTRACT.md` exactly.

## Testing without the real backend

`mock_backend/mock_server.py` is a small FastAPI app that mimics the real contract, for testing the UI in
isolation. It's not the real backend and has no bisection or Bob logic — just the same shapes and timing.

```
cd mock_backend && pip install -r requirements.txt && python mock_server.py
```
Then open `http://127.0.0.1:5500/index.html?api=http://127.0.0.1:8000`. Useful env vars for testing:
`MOCK_SPEED=3` (faster), `MOCK_NO_WS=1` (force the polling fallback), `MOCK_COLDSTART=7` (simulate a slow
first response), `MOCK_UNKNOWN_REPO=1` (simulate the repo-not-found case).

For a quick look with no server running at all, press **D** on the page for a labelled "Simulated sample"
replay — never use this for the actual judged demo.

## What to do after this, in order

1. **Run "Test backend connection."** Fix whatever it flags before anything else.
2. **Run a real investigation** with the Sample input. Confirm the chip says **Live** (not stuck on Polling)
   and that a report appears.
3. **If it fails**, check the Event feed panel and this README's "Known thing I could not verify" section
   first — most likely cause is the demo repo path.
4. **Do the Bob IDE work and evidence capture** for BOB_STEPS.md — that part is yours to run and screenshot
   into `bob_sessions/`, since it has to be a real Bob session to count as evidence.
5. **Record the demo** (script below) using the real backend run, not the "D" replay.
6. **Submit** the repo with `bob_sessions/` included. Check your team's actual deadline first.

## 3-minute demo script

- 0:00 Problem: a failing test costs 1 to 4 hours of bug hunting.
- 0:20 Paste the failing test and error log, press Open investigation.
- 0:40 Point at the bisection strip: Bob walks the git history, one commit tile flips per check.
- 1:10 The Detective Lineup: four hypotheses tested in parallel, columns climbing toward the 85% line.
- 1:50 The moment: one column crosses 85%, turns yellow, the camera swings to it, the others go grey and are ruled out.
- 2:15 Case file unfolds: culprit commit, plain-English cause, fix diff, regression test.
- 2:45 Close: show the `bob_sessions/` folder and say where Bob was used (Plan mode, subagents, Agent mode).

## Frontend brief checklist

| Brief step | Status | Where |
| --- | --- | --- |
| A. Document understanding of the contract | Done | ROOTCAUSE_API_CONTRACT.md, ready for Bob |
| B. Plan-mode prompt | Prepared | BOB_STEPS.md (theme changed to light on purpose) |
| B1. Form: repo_path, failing_test, error_log to POST /api/investigate | Done | "New investigation" card |
| B2. Four hypothesis cards, animated 0-100% bar, status badge | Done | 3D columns plus a bar and badge per card |
| B3. Bisection bar, commits_checked / total_commits | Done | "Git bisection" |
| B4. Report: commit_hash, root_cause_label, explanation, fix_diff, regression_test | Done | "Case file" |
| C. Single index.html, embedded style and script | Done | index.html |
| D. ~85% CONFIRMED glow, other three fade to ruled out | Done | Detective Lineup |
| E. "Checking commit {hash} — {n}/{total}." | Done | first 8 characters shown, full hash on hover |
| F. fix_diff and regression_test in monospace pre blocks, +/- colours | Done | IBM Plex Mono |
| G. WebSocket, routeEvent on "type", polling fallback every 1000 ms | Done, tested | startPollingFallback(id, 1000) |
| H. Submit, store investigation_id, open WebSocket, render live | Done, tested | form handler |
| Connect to the real deployed backend | Done | default API = https://ibm-bob-backend.onrender.com |
| Cold-start handling for free hosting | Done, tested | 70s timeout, "waking up" note after 6s |
| Self-serve connection diagnostics | Done, tested | "Test backend connection" button |
| Evidence: bob_sessions/ screenshots | Yours to do | see step 4 above |

Deliberate difference from the brief: light theme instead of dark, as you asked.

## Troubleshooting

- "Could not open the case": either the backend is still waking up (wait ~50s and retry) or CORS/origin is
  wrong. Run "Test backend connection" to tell which.
- Banner about "could not find the repository": the demo repo path in this build (`/tmp/rootcause-demo-repo`)
  doesn't exist on the running Render instance. Ask your backend teammate to confirm the Start Command runs
  the demo-repo setup script before `uvicorn`.
- Chip says Polling instead of Live: the WebSocket at `wss://ibm-bob-backend.onrender.com/ws/investigation/{id}`
  isn't connecting, but the page still works via polling every second.
- Bars never move: confirm `confidence` is sent as 0 to 100.
- Point at a different backend for testing: open the page with `?api=http://127.0.0.1:8000` (or any other URL).
- Keys: **D** demo replay, **N** reset, **M** motion off, **Ctrl+Enter** submit. Drag the 3D scene to rotate it.
