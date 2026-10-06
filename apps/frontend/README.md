# F1 ERAs frontend

React, TypeScript, Vite, and Plotly render the curated 2010–2013 Original Drivers
championship margins supplied by the FastAPI backend. The frontend uses the API's
plot values for chart geometry; it does not calculate points or margins.
This is the first visible slice of v1's historical champion-versus-runner-up
comparison, not the complete v1 product. See the [roadmap](../../docs/README.md)
and [Milestone 2](../../docs/decisions/MILESTONE_2_DECISION_RECORD.md) for remaining work.

## Run locally

Follow [Development Setup](../../SETUP.md) for prerequisites and dependency
installation, manual startup and the root Windows/macOS/Linux launchers. That guide
is the single environment authority; routine startup does not reinstall dependencies.

Open `http://127.0.0.1:5173/`. Vite proxies `/api` to the backend at
`http://127.0.0.1:8000`, so browser CORS configuration is unnecessary for this
local setup. The backend reads the repository's `data/f1db.db` by default;
the [backend reference](../backend/README.md) describes source overrides and trust.

## Verify

Run from the repository root:

```powershell
npm.cmd --prefix apps/frontend test
npm.cmd --prefix apps/frontend run build
```

The build command checks TypeScript and produces `dist/`. The only charted
category is Drivers; Constructors is visibly unavailable. The only scoring
context is Original. The metric toggle selects backend-provided Championship
Margin (%) or raw Points Gap plotting values. Unsupported response items display
their API reason without a fabricated chart value.

## Integration and current limits

`src/api/client.ts` fetches the Drivers / Original margin summaries and validates
the fields this slice consumes. `App.tsx` manages metric, loading/error/retry and
availability state. `chartModel.ts` builds independent zero-based lollipop stems
and P1/P2 hover text from API values; `ChampionshipMarginChart.tsx` renders Plotly.
Tests cover that interaction and geometry with mocked fetch/Plotly, not a real
browser end-to-end run. The build includes the TypeScript compiler checks.

The frontend does not yet use capabilities to drive range controls, fetch season
detail, or expose the backend's teammate/trust metadata. Team colours, nationality,
era/range navigation, pinned selection and a detail drawer remain target work.
The existing responsive chart and text list are a starting point, not evidence of
complete accessibility or small-screen validation.

The disabled Constructors button is a PoC placeholder for unimplemented v3 scope;
it does not make Constructors analytics a v1 requirement. Alternative scoring
controls belong to v2. The master brief defines the
[visible analytical contract](../../docs/architecture/F1_ERAs_MASTER_BRIEF.md#v1-visible-analytical-contract).
