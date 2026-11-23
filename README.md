# SmartFactory - Order-to-Audit ERP

**An integrated ERP demonstration for a South Indian packaged-food manufacturer.**

SmartFactory is an internship demonstration project that connects factory operations, inventory, production, sales, GST billing, payments and audit management in one application.

It combines a React-based, role-aware frontend with a FastAPI backend and SQLAlchemy database layer. The application demonstrates how business transactions can be tracked from purchasing raw materials through production, order fulfilment, invoicing and payment collection.

## 1. Technology Stack

| Component | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Backend | Python 3.12, FastAPI |
| Database | SQLite, SQLAlchemy |
| Authentication | JWT bearer tokens |
| Package manager | pnpm 11.25.0 |
| Testing | pytest |
| Reports | CSV, Excel (XLSX), PDF |
| API documentation | FastAPI Swagger UI |
| Containerization | Docker |

## 2. Requirements

Install the following software before running the application:

- Python 3.11 or later (tested with Python 3.12)
- Node.js 20 or later
- pnpm 11.25.0
- Visual Studio Code (recommended)
- Git (recommended)
- Docker (optional, for containerized deployment)

Check the installed versions:

```powershell
python --version
node --version
pnpm --version
```

The frontend declares `pnpm@11.25.0` in its `package.json`. Using that version is recommended for consistent dependency installation.

## 3. Installation on Windows

Open PowerShell in the SmartFactory project directory.

### Step 1: Create the Python virtual environment

```powershell
py -3.11 -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the virtual environment again.

### Step 2: Install backend dependencies

From the project root:

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

### Step 4: Configure environment variables

The project includes an `.env.example` template.

Create a local copy:

```powershell
Copy-Item .env.example .env
```

The template documents these settings:

| Variable | Purpose |
|---|---|
| `JWT_SECRET` | Secret used for JWT authentication |
| `SMARTFACTORY_DATABASE_URL` | Database connection string |

The example database configuration uses SQLite:

```text
SMARTFACTORY_DATABASE_URL=sqlite:///./smartfactory.db
```

The example JWT secret is a placeholder. Replace it with a unique, strong secret before deployment.

Set environment variables in the PowerShell session when required:

```powershell
$env:JWT_SECRET = "replace-with-your-own-long-random-secret"
$env:SMARTFACTORY_DATABASE_URL = "sqlite:///./smartfactory.db"
```

These PowerShell variables apply to the current terminal session.

## 4. Run the Application

SmartFactory uses two development servers. Keep both terminals open while working.

### Terminal 1 - Start the backend

From the project root directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --log-level debug --access-log
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

`http://localhost:5174`

The Vite development server proxies API requests to the backend running on port `8002`.

### API documentation

Swagger UI:

`http://127.0.0.1:8002/docs`

The documentation provides access to the available API endpoints, request parameters and response schemas.

## 5. Demo Accounts

Use the following seeded demonstration accounts to explore the role-based application.

| Role | Email | Password |
|---|---|---|
| Admin | `admin@smartfactory.local` | `Admin123!` |
| Owner | `owner@smartfactory.local` | `Owner123!` |
| Production Supervisor | `production@smartfactory.local` | `Prod123!` |
| Salesman A | `sales.a@smartfactory.local` | `Sales123!` |
| Salesman B | `sales.b@smartfactory.local` | `Sales123!` |
| Accountant / Auditor | `audit@smartfactory.local` | `Audit123!` |

These credentials are for demonstration purposes only.

Replace seeded passwords, configure a strong JWT secret and review access permissions before any public or production deployment.

## 6. Database

SQLite is used as the default database for the demonstration environment.

Default database file:

`smartfactory.db`

The application uses SQLAlchemy for database operations.

### Demonstration data

The seeded demonstration environment includes:

- Role-based user accounts
- Retailer A in Tamil Nadu
- Distributor B in Karnataka
- Murukku 200 g finished product
- Bill of Materials (BOM)
- Opening raw-material inventory
- Opening finished-goods inventory

### Database configuration

The application supports database configuration through:

`SMARTFACTORY_DATABASE_URL`

Example SQLite connection string:

```text
sqlite:///./smartfactory.db
```

Example PostgreSQL connection string:

```text
postgresql+psycopg://user:password@host:5432/smartfactory
```

For PostgreSQL deployments, install the appropriate PostgreSQL driver and configure the database connection securely.

SQLite is intended for the single-instance demonstration environment. For multi-instance deployments, use a suitable shared database such as PostgreSQL.

Apply appropriate database migrations and configure backups before production use.

## 7. Benchmark Scenario

Sign in as Admin or Owner and select **Run Benchmark** from the Overview or Production section.

The benchmark demonstrates the supplied factory scenario:

1. Purchase 60 kg of flour at Rs.45 per kg.
2. Issue raw materials for production.
3. Record 40 kg flour consumption.
4. Record 10.5 L cooking oil consumption.
5. Record 1.2 kg spice consumption.
6. Record labour cost of Rs.1,200.
7. Record utilities cost of Rs.600.
8. Produce 188 good packets from an expected output of 200 packets.
9. Create, approve, invoice and dispatch Retailer A's order for 150 packets.
10. Create Distributor B's order for 120 packets and demonstrate the stock shortage.
11. Record a payment collection of Rs.4,000.

### Expected benchmark results

| Metric | Expected result |
|---|---:|
| Flour stock | 120 kg |
| Flour weighted-average cost | Rs.43.125/kg |
| Cooking oil stock | 19.5 L |
| Spice stock | 3.8 kg |
| Pouches | 306 pieces |
| Available pouches | 300 pieces |
| Quarantined damaged pouches | 6 pieces |
| Cartons | 21 pieces |
| Finished goods after dispatch | 88 packets |
| Production yield variance | -6% |
| Cooking oil consumption variance | +5% |
| Invoice taxable value | Rs.7,500 |
| CGST | Rs.187.50 |
| SGST | Rs.187.50 |
| Invoice total | Rs.7,875 |
| Payment received | Rs.4,000 |
| Outstanding amount | Rs.3,875 |
| Distributor B shortage | 32 packets |
| Total production cost | Rs.5,870 |
| Production cost per packet | Rs.31.22 |

**Important:** Running the benchmark resets the demonstration database and recreates its sample scenario. Do not run it against live business data or a database containing information you need to preserve.

For details about stock reconciliation, weighted-average costing and quality-control quarantine, see `docs/design-note.md`.

## 8. Main Application Features

### Dashboard

- Factory operations overview
- Sales and receivables summary
- Finished-goods stock visibility
- Inventory warnings
- Production alerts

### Sales Order Management

- Create and track sales orders
- Review and approve orders
- Detect insufficient finished-goods stock
- Dispatch approved orders
- Track order status and transaction history

### Production Management

- BOM-based production planning
- Raw-material consumption tracking
- Good-output recording
- Damaged-pouch recording
- Yield and consumption variance monitoring
- Production cost calculation

### Inventory Management

- Raw-material and finished-goods tracking
- Stock movement ledger
- Stock adjustments
- Weighted-average costing
- Quality-control quarantine tracking

### GST Billing

- GST invoice generation
- CGST and SGST for applicable intra-state transactions
- IGST handling for applicable inter-state transactions
- Invoice PDF export
- Payment and outstanding-balance tracking

### Reports and Audit

- Production reports
- Inventory reports
- Consumption and yield reports
- Cost-per-packet reports
- CSV exports
- Excel exports
- PDF exports
- Audit trail visibility

## 9. API Endpoints

The backend exposes REST API endpoints through FastAPI.

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/login` | User authentication |
| `GET /api/auth/me` | Current user profile |
| `GET /api/dashboard` | Dashboard information |
| `/api/bom` | Bill of Materials |
| `/api/orders` | Sales order management |
| `/api/purchases` | Purchase management |
| `/api/production` | Production operations |
| `/api/inventory/adjustments` | Inventory adjustments |
| `/api/orders/{id}/decision` | Order approval or rejection |
| `/api/orders/{id}/invoice` | Invoice generation |
| `/api/orders/{id}/dispatch` | Order dispatch |
| `/api/payments/{invoice_id}` | Payment collection |
| `/api/invoices/{id}/pdf` | Invoice PDF generation |
| `/api/reports/{report}` | Report generation |
| `/api/audit` | Audit records |
| `POST /api/benchmark/run` | Demonstration benchmark |

For complete request and response schemas, open:

`http://127.0.0.1:8002/docs`

## 10. Run Tests

From the project root with the virtual environment activated:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The test suite covers:

- Benchmark figures
- Inventory and production behavior
- Transaction rollback for insufficient stock
- Read-only auditor permissions

### Financial and audit design

- Financial values are stored in integer paisa.
- Weighted-average costing uses Decimal calculations.
- Stock movements are tracked through inventory records.
- Posted invoices are retained on cancellation to preserve the audit trail.
- A production-ready credit-note and goods-return workflow is required for post-dispatch corrections.

## 11. Build the Frontend

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

The development server and production build serve different purposes:

- Development: Vite serves the React application on port `5174`.
- Production: FastAPI can serve the built frontend assets.

## 12. Docker Deployment

The project includes a multi-stage Dockerfile.

The first stage:

- Uses Node.js 22.
- Installs pnpm 11.25.0.
- Installs frontend dependencies.
- Builds the React frontend.

The second stage:

- Uses Python 3.12.
- Installs backend dependencies.
- Copies the FastAPI application.
- Copies the compiled frontend build.
- Starts the application using Uvicorn.

### Build the Docker image

Run from the project root:

```powershell
docker build -t smartfactory .
```

### Run the container

```powershell
docker run --rm -p 3000:3000 -e JWT_SECRET="replace-with-a-strong-secret" smartfactory
```

Open the application:

`http://localhost:3000`

The container exposes port `3000`. FastAPI serves the built frontend and backend API from the same application.

**Database persistence:** The default SQLite database is stored inside the container's working directory. Data may be lost when a replaceable container is removed. Configure persistent storage or an external database before using Docker for any environment where data must be retained.

## 13. Deployment and Security

SmartFactory is an internship demonstration project and should not be used as-is for production business operations.

Before using it in a real business environment:

- Configure a strong, unique `JWT_SECRET`.
- Replace demonstration user passwords.
- Use a durable database such as PostgreSQL for multi-instance deployments.
- Configure HTTPS and secure ingress.
- Protect credentials using environment variables or a deployment secret manager.
- Configure database backups and recovery procedures.
- Apply database migrations.
- Implement appropriate rate limiting and monitoring.
- Review role permissions and audit controls.
- Validate GST tax master data with a qualified accountant.
- Complete the credit-note and goods-return workflows.
- Perform a security review before handling real business data.

## 14. Project Structure

The main project directories are organized as follows:

```text
smartfactory/
│
├── app/                    # FastAPI backend
├── frontend/               # React + TypeScript frontend
│   ├── src/                # Frontend source code
│   └── dist/               # Production build output
│
├── docs/                   # Project documentation
├── tests/                  # Automated backend tests
│
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── Dockerfile              # Multi-stage Docker build
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
└── smartfactory.db         # Local SQLite database (generated)
```

Generated files and local environment directories are excluded from Git through `.gitignore`.

## 15. Project Documentation

Additional documentation is available in the `docs` directory.

| File | Description |
|---|---|
| `docs/architecture.md` | System architecture and entity relationship diagram |
| `docs/design-note.md` | BOM, inventory reconciliation, costing and GST design |
| `docs/demo-script.md` | Eight-minute demonstration walkthrough |

---

**SmartFactory - Order-to-Audit ERP**

An integrated demonstration of factory operations, production, inventory, sales, GST billing, payment collection and audit management.