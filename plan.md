# SmartFactory implementation plan

## Scope and architecture
Build a functional demonstration ERP, prioritizing correct, explainable production and stock accounting, then the order-to-invoice-to-payment flow and report exports. Use a React + Vite + TypeScript frontend styled with Tailwind CSS and Recharts. Use Python FastAPI + SQLAlchemy + SQLite for the backend; preserve portability through a `DATABASE_URL` environment variable and PostgreSQL-compatible SQLAlchemy types. Use JWT bearer tokens, role checks, integer paisa for money, and a SQLite transaction for each production/dispatch/payment operation. Generate invoice PDFs with ReportLab and tabular exports with Pandas (CSV/Excel); expose Swagger/OpenAPI at `/docs`.

The seeded demo will provide the exact benchmark master data and a repeatable “Run benchmark” action. Production is the source of truth for stock: purchases/production/dispatch create linked ledger movements; users never edit balances in place. Flour uses the given opening valuation of ₹42/kg and 60 kg purchased at ₹45/kg, resulting in weighted-average ₹43.125/kg. GST uses 5%, split equally as CGST/SGST for Tamil Nadu and IGST for inter-state transactions. Quantities and money are validated and business errors surfaced to the UI. A single FastAPI process serves the compiled React app at the configured port; `/api` and `/docs` remain available. Local setup and production/container deployment instructions will be documented; publication remains a distinct platform operation.

## Project structure
- `app/`: FastAPI application, SQLAlchemy models/session, authentication/authorization, business services, PDF/report endpoints, seed and benchmark logic.
- `frontend/src/`: React role-aware dashboard, navigation, benchmark operations, tables/forms/charts and API client.
- `frontend/`: Vite, Tailwind, TypeScript and production build.
- `tests/`: automated checks for benchmark stock, GST arithmetic, weighted-average costing, production variance and role/business rules.
- Root docs: `README.md`, this plan, `TODO.md`, `docs/architecture.md`, `docs/design-note.md`, `docs/demo-script.md`, and `.env.example`.

## Design
- **Movement:** Calm industrial operations console, with familiar factory-control-room cues.
- **Core principles:** Legible at a glance; high information density without clutter; important stock and variance events have clear status; actions expose their ledger/document consequence.
- **Color philosophy:** White and warm-gray canvas with navy structure for trust and focus; restrained teal for healthy operations and amber/red only for attention and risk.
- **Layout paradigm:** Fixed left navigation rail and a broad, asymmetric work surface: compact summary strip, dominant operational chart/queue, and a right-side attention column; collapses to a bottom/compact navigation on small screens.
- **Signature elements:** Small numbered process markers for order-to-audit progression; consistent document-reference chips on inventory movements; compact variance meters with a 3% threshold.
- **Interaction philosophy:** Quick actions open short validated forms, destructive/posted operations are explicit, and updates visibly change counts and stock rather than pretending success.
- **Animation:** Brief (120–180 ms) opacity/position transitions for menus and panels; no continuous animation; honor reduced-motion settings.
- **Typography system:** Inter for UI/body, Space Grotesk for headline/number emphasis; tabular numerals for quantities and money; clear 12/14/16/22/30 px hierarchy.
- **Brand essence:** A practical, auditable factory operating desk for small packaged-food manufacturers; **precise, grounded, capable**.
- **Brand voice:** Direct operational language. Examples: “Production variance needs a look.” “Post movement to the ledger.”
- **Wordmark & logo:** A custom inline mark combining three navy production lanes with a teal check/flow line beside the SmartFactory wordmark.
- **Signature brand color:** Deep process navy, paired with a restrained process-teal accent.

## Runtime and build workflow
Pin pnpm in the frontend manifest and lockfile, configure lifecycle-script policy before installing dependencies, register TypeScript diagnostics, and add a complete route manifest before starting Preview. Build and serve the React output through FastAPI on the configured port 3000; declare that foreground command with `webdev.config` and verify the health endpoint and route manifest over HTTP. Run automated tests and build checks. Preserve changes on `main` by integrating `origin/main` and pushing the deliverable checkpoint. The request asks for deployment; prepare the container/static build configuration and publish only after the implementation is verified, checking the actual publish result before reporting a URL.

## Material constraints
The managed database resource is enabled, but its access method is not assumed: keep the SQLAlchemy URL configurable and use local SQLite by default for reproducible benchmark/demo data. This version is an internship demonstration, not a legal determination of GST compliance; production tax rates, HSN/GSTIN master data, rounding, credit notes and accounting policies need accountant review. Implement cancellation as an auditable status/action, never deletion of posted invoices. The project is new/empty, so restart is possible only after the server command and app are created.