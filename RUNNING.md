# Running FitFindr v2

This is the Unit 9 local-with-logs path. The original setup guide is preserved in [docs/unit3-running-original.md](docs/unit3-running-original.md).

## Clean checkout and environment

Tested on Windows with Python 3.13.3. Python 3.11-3.13 is the original supported range; other OS/Python combinations have not been verified in this change. No local model weights are used. Both JSON data files are tracked in `data/`; there is no database or separate catalog download. Tracked data: `listings.json` (19,171 bytes), `wardrobe_schema.json` (3,381 bytes).

```powershell
git clone --branch codex/unit9-budget-outfits https://github.com/winaung786/ai201-project2-fitfindr-starter-v2026.git
cd ai201-project2-fitfindr-starter-v2026
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
```

On macOS/Linux, use `python3 -m venv .venv` and `source .venv/bin/activate`, then the same install command. `requirements-lock.txt` pins the versions installed for this build; the Windows-only package has a platform marker. The original bounded dependency declarations remain in `requirements.txt`. Do not upgrade packages while reproducing measurements.

Budget previews need **no environment variables or API key**. The existing single-item model path loads a private `GEMINI_API_KEY` from `.env` if provided (copy `.env.example` and edit locally). Never commit that file. Without a key the original text tools provide local fallbacks; a fallback run is not a live model evaluation.

## Start command

From the repository root with the environment activated:

```powershell
$env:FITFINDR_LOG_PATH = 'logs/runs.jsonl'
python serve.py
```

It listens on `http://localhost:5000`, binds `0.0.0.0`, and writes JSON logs to stderr and the optional local file. `PORT` changes the port. `AI201_DEBUG` is off by default. Keep it off for shared machines. Stop with Ctrl+C. On Linux hosting, use one synchronous worker: `gunicorn --workers 1 --timeout 150 serve:app`. Async workers are incompatible with the existing MCP client. The app is designed for local use; public deployment would require authentication and request/rate controls.

In another PowerShell terminal:

```powershell
Invoke-RestMethod http://localhost:5000/health
$body = '{"query":"Find me a casual outfit under $100"}'
$result = Invoke-RestMethod http://localhost:5000/ask -Method Post -ContentType 'application/json' -Body $body
$result.budget_result
$result.outfit_suggestion
$result.fit_card
```

To supply the total separately and filter each clothing category:

```json
{"query":"casual outfit","budget":"100.00","sizes":{"tops":"M","bottoms":"W30","shoes":"US 9"}}
```

The `sizes` object is optional. One size cannot describe all three categories; `outfit size M` is rejected with a category-size instruction. Budget searches never drop a size filter. The existing single-item route retains its disclosed one-time size retry.

HTTP statuses: 200 for a successful budget preview; 400 for bad input or an invalid/absent/conflicting budget; 422 for no complete valid outfit in the returned candidates; 503 for a failed budget tool; 413 for a body above 32 KB. The legacy route retains its session `error` contract; always inspect it. Logs and response metrics share a run ID.

## Command-line preview

```powershell
python app.py ask 'Find me a casual outfit under $100' --trace
python app.py ask 'casual outfit' --budget 100
python app.py ask 'casual outfit under $1'
python app.py ask 'vintage graphic tee under $30, size M'
```

Use single quotes so PowerShell does not expand the dollar amount. Whole-outfit budgets are positive USD merchandise subtotals, with at most two decimals, and an inclusive cap. Taxes/shipping are excluded. The sample catalog has no live availability or product links; the preview states that limitation. Missing/invalid prices, unavailable items and non-USD currencies are excluded rather than estimated. A low budget produces a clear error and no partial fit card. Wardrobe costs are not used in the budget preview: all three selected pieces come from listings.

## Verification and measurements

```powershell
python -m unittest discover -s tests -v
python scripts/measure_budget.py
```

The regression suite uses in-process replacements for MCP transport and does not call a model. It covers exact/over-budget boundaries, missing prices, unavailable items, alternate combinations, HTTP rejection and log privacy. The measurement command performs ten separate real-MCP outfit runs plus one deliberate invalid-budget failure, writing `results/unit9-build-cost.json` and `.jsonl`; rerunning intentionally replaces these build measurement files. Use `--output logs/my-cost.json` to preserve committed evidence. No model/cache calls occur in the budget path. Parent CPU excludes MCP child processes; elapsed time includes startup and waiting. Without a compute tariff, CPU/elapsed time cannot be converted to dollars.

The committed build evidence is separate from the student-authored capstone acceptance results. Write/commit Unit 9 criteria before the formal acceptance baseline; the original `criteria.md` is still the Unit 3/4 file. Follow [docs/unit9-plan.md](docs/unit9-plan.md) to complete that part later.

Logs use UTC timestamps and allowlisted fields. Query text is replaced by its SHA256 and length; wardrobe contents and credentials are omitted. Review evidence before committing. Local log files are not rotated automatically; remove or archive `logs/` when appropriate. If a log file cannot be written, stderr remains the log sink.
