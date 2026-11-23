# SmartFactory - Order-to-Audit ERP

SmartFactory is an internship demonstration ERP for a South Indian packaged-food manufacturer. It combines a React role-aware workspace with a FastAPI and SQLAlchemy backend.

The application demonstrates order management, inventory tracking, BOM-based production, weighted-average material costing, GST invoicing, payment collection, audit trails and downloadable reports.

## 1\. Technology Stack

|Component|Technology|
|-|-|
|Frontend|React 18, TypeScript, Vite|
|Backend|Python, FastAPI|
|Database|SQLite, SQLAlchemy|
|Authentication|JWT bearer tokens|
|Package manager|pnpm|
|Testing|pytest|
|Reports|CSV, Excel (XLSX), PDF|
|API documentation|Swagger UI|

## 2\. Requirements

Install the following before running the application:

* Python 3.11 or later
* Node.js 20 or later
* pnpm
* Visual Studio Code (recommended)

Check your installed versions:

```powershell
python --version
node --version
pnpm --version
```

## 3\. Installation on Windows

Open PowerShell in the SmartFactory project directory.

### Step 1: Create the Python virtual environment

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\\.venv\\Scripts\\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### Step 2: Install backend dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Install frontend dependencies

```powershell
cd frontend
pnpm install --frozen-lockfile
cd ..
```

## 4\. Run the Application

SmartFactory uses two development servers. Keep both terminals open while working.

### Terminal 1 - Start the backend

From the project root directory:

```powershell
.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --log-level debug --access-log
```

The backend runs at:

`http://127.0.0.1:8002`

Health check:

`http://127.0.0.1:8002/health`

### Terminal 2 - Start the frontend

Open another PowerShell terminal:

```powershell
cd frontend
pnpm run dev -- --port 5174
```

Open the application in your browser:

**http://localhost:5174**

The Vite development server proxies API requests to the backend running on port 8002.

### API documentation

Swagger UI:

`http://127.0.0.1:8002/docs`

This provides access to the available API endpoints and request schemas.

## 5\. Demo Accounts

Use the following seeded demonstration accounts to explore the role-based application.

|Role|Email|Password|
|-|-|-|
|Admin|`admin@smartfactory.local`|`Admin123!`|
|Owner|`owner@smartfactory.local`|`Owner123!`|
|Production Supervisor|`production@smartfactory.local`|`Prod123!`|
|Salesman A|`sales.a@smartfactory.local`|`Sales123!`|
|Salesman B|`sales.b@smartfactory.local`|`Sales123!`|
|Accountant / Auditor|`audit@smartfactory.local`|`Audit123!`|

These credentials are for demonstration purposes only. Replace seeded passwords and configure a strong JWT secret before any public or production deployment.

## 6\. Database

SQLite is used as the default database.

The database file is created in the project working directory:

`smartfactory.db`

The application uses SQLAlchemy for database operations.

The demonstration data includes:

* Role-based user accounts
* Retailer A in Tamil Nadu
* Distributor B in Karnataka
* Murukku 200 g product and BOM
* Opening raw-material and finished-goods stocks

For deployments requiring multiple application instances, configure `SMARTFACTORY\_DATABASE\_URL` with a suitable PostgreSQL connection string and install the appropriate PostgreSQL driver. Apply database migrations before production use.

## 7\. Benchmark Scenario

Sign in as Admin or Owner and select **Run Benchmark** from the Overview or Production section.

The benchmark executes the supplied factory scenario:

1. Purchase 60 kg of flour at Rs.45 per kg.
2. Issue raw materials for production.
3. Record 40 kg flour, 10.5 L cooking oil and 1.2 kg spice consumption.
4. Record labour cost of Rs.1,200 and utilities cost of Rs.600.
5. Produce 188 good packets from an expected output of 200 packets.
6. Create, approve, invoice and dispatch Retailer A's order for 150 packets.
7. Create Distributor B's order for 120 packets and demonstrate the stock shortage.
8. Record a payment collection of Rs.4,000.

**Important:** Running the benchmark resets the demonstration database and recreates its sample scenario. Do not use this action with live business data.

### Expected Benchmark Results

|Metric|Expected result|
|-|-:|
|Flour stock|120 kg|
|Flour weighted-average cost|Rs.43.125/kg|
|Cooking oil stock|19.5 L|
|Spice stock|3.8 kg|
|Pouches|306 pieces|
|Available pouches|300 pieces|
|Quarantined damaged pouches|6 pieces|
|Cartons|21 pieces|
|Finished goods after dispatch|88 packets|
|Production yield variance|-6%|
|Cooking oil consumption variance|+5%|
|Invoice taxable value|Rs.7,500|
|CGST|Rs.187.50|
|SGST|Rs.187.50|
|Invoice total|Rs.7,875|
|Payment received|Rs.4,000|
|Outstanding amount|Rs.3,875|
|Distributor B shortage|32 packets|
|Total production cost|Rs.5,870|
|Production cost per packet|Rs.31.22|

See `docs/design-note.md` for the stock reconciliation, costing and quarantine explanation.

## 8\. Main Application Features

### Dashboard

* Factory operations overview
* Sales and receivables summary
* Finished-goods stock visibility
* Inventory warnings and production alerts

### Sales Order Management

* Create and track sales orders
* Review and approve orders
* Detect insufficient finished-goods stock
* Dispatch approved orders

### Production Management

* BOM-based production planning
* Raw-material consumption tracking
* Good output and damaged-pouch recording
* Yield and consumption variance monitoring
* Production cost calculation

### Inventory Management

* Raw-material and finished-goods tracking
* Stock movement ledger
* Stock adjustments
* Weighted-average costing
* Quality-control quarantine tracking

### GST Billing

* GST invoice generation
* CGST and SGST for applicable intra-state transactions
* IGST handling for applicable inter-state transactions
* Invoice PDF export
* Payment and outstanding balance tracking

### Reports and Audit

* Production reports
* Inventory reports
* Consumption and yield reports
* Cost-per-packet reports
* CSV, Excel and PDF exports
* Audit trail visibility

## 9\. API Endpoints

The backend exposes REST API endpoints through FastAPI.

|Endpoint|Purpose|
|-|-|
|`POST /api/auth/login`|User authentication|
|`GET /api/auth/me`|Current user profile|
|`GET /api/dashboard`|Dashboard information|
|`/api/bom`|Bill of Materials|
|`/api/orders`|Sales order management|
|`/api/purchases`|Purchase management|
|`/api/production`|Production operations|
|`/api/inventory/adjustments`|Inventory adjustments|
|`/api/orders/{id}/decision`|Order approval or rejection|
|`/api/orders/{id}/invoice`|Invoice generation|
|`/api/orders/{id}/dispatch`|Order dispatch|
|`/api/payments/{invoice\_id}`|Payment collection|
|`/api/invoices/{id}/pdf`|Invoice PDF|
|`/api/reports/{report}`|Report generation|
|`/api/audit`|Audit records|
|`POST /api/benchmark/run`|Demonstration benchmark|

For complete request and response schemas, open:

`http://127.0.0.1:8002/docs`

## 10\. Run Tests

From the project root with the virtual environment activated:

```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q
```

The test suite covers benchmark figures, inventory and production behavior, transaction rollback for insufficient stock and read-only auditor permissions.

Financial values are stored in integer paisa, and weighted-average costing uses Decimal calculations.

Posted invoices are retained on cancellation to preserve the audit trail. A production-ready credit-note and goods-return workflow is required for post-dispatch corrections.

## 11\. Build the Frontend

To create a production frontend build:

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm run build
cd ..
```

The build output is generated in:

`frontend/dist`

The backend can serve the built frontend when that directory is available at application startup.

## 12\. Deployment and Security

Before using SmartFactory in a real business environment:

* Configure a strong `JWT\_SECRET`.
* Use a durable database such as PostgreSQL for multi-instance deployments.
* Configure HTTPS and secure ingress.
* Protect credentials using environment variables or a deployment secret manager.
* Configure database backups and recovery procedures.
* Apply database migrations.
* Implement appropriate rate limiting and monitoring.
* Review permissions and audit controls.
* Validate GST tax master data with an accountant.
* Complete the credit-note and goods-return workflows.
* Perform a security review before handling real business data.

SQLite is intended for the single-instance demonstration environment. Container-local database files may be lost when the container is replaced unless persistent storage is configured.

## 13\. Project Documentation

Additional documentation is available in the `docs` directory:

|File|Description|
|-|-|
|`docs/architecture.md`|System architecture and entity relationship diagram|
|`docs/design-note.md`|BOM, inventory reconciliation, costing and GST design|
|`docs/demo-script.md`|Eight-minute demonstration walkthrough|

\---

**SmartFactory - Order-to-Audit ERP**

An integrated demonstration of factory operations, production, inventory, sales, GST billing and audit management.

