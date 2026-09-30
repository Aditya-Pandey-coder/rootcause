# RootCause frontend: run these in IBM Bob IDE, one session per step

Screenshot each session into `bob_sessions/` as you go (Bob IDE: Tasks > select task > click header for the task session summary).
Use only the hackathon-provisioned Bob account. Name files like `cryptix_stepB_plan_summary.png`.

## Step A: Document understanding (no prompt yet)
Open the folder in Bob IDE. Point Bob at `ROOTCAUSE_API_CONTRACT.md` so every field it renders is the real schema.
Capture: screenshot of Bob reading the file.

## Step B: Plan mode (paste as one prompt)
Changed from the brief on purpose: light theme, minimal, 3D (the brief said dark).
```
Plan a single-file HTML/CSS/vanilla-JS dashboard called RootCause, matching the schemas in ROOTCAUSE_API_CONTRACT.md exactly. It needs: (1) an input form for repo_path, failing_test, error_log that POSTs to /api/investigate; (2) a "Detective Lineup" panel with 4 hypothesis cards (race_condition, dependency_bump, off_by_one, api_contract_break), each with a live animated confidence bar 0-100% and a status badge (testing/confirmed/ruled out); (3) a bisection progress bar showing commits_checked / total_commits; (4) a final report panel showing commit_hash, root_cause_label, explanation, fix_diff, and regression_test in monospace code blocks. It connects to ws://127.0.0.1:8000/ws/investigation/{id} for live updates, with a polling fallback to GET /api/investigation/{id}/status if the socket disconnects. Light theme, minimalist, 3D investigation-board aesthetic. Produce a written plan before any code.
```
Approve the plan before moving on.

## Step C: Agent mode, skeleton
```
Implement the approved plan as a single index.html with embedded <style> and <script>, no external build tools, no frameworks.
```

## Step D: Detective Lineup (polish most)
```
4 cards in a row, one per hypothesis. Confidence bars animate smoothly as WebSocket events arrive. The card that crosses ~85% gets a CONFIRMED glow; the other 3 visibly fade to ruled out.
```

## Step E: Bisection bar
```
A horizontal bar with the label: Checking commit {commit_hash} — {commits_checked}/{total_commits}.
```

## Step F: Final report panel
```
Render fix_diff and regression_test inside monospace <pre> blocks, with +/- diff line colours.
```

## Step G: WebSocket + polling fallback
```
const ws = new WebSocket(`ws://127.0.0.1:8000/ws/investigation/${id}`);
ws.onmessage = (e) => routeEvent(JSON.parse(e.data));
ws.onerror = ws.onclose = () => startPollingFallback(id, 1000);
```

## Step H: Wire the form
```
On submit: POST to http://127.0.0.1:8000/api/investigate, store investigation_id, open the WebSocket with that id, render everything live.
```

Serve with `python -m http.server 5500`, open http://127.0.0.1:5500 (never file://).
