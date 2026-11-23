# Architecture

```mermaid
flowchart LR
  Browser[React + Tailwind + Recharts\nRole-aware workspace] -->|Bearer JWT / JSON| API[FastAPI\nBusiness rules + validation]
  API --> ORM[SQLAlchemy\nTransactional services]
  ORM --> DB[(SQLite demo\nPostgreSQL URL migration path)]
  API --> PDF[ReportLab\nInvoice and PDF reports]
  API --> DF[Pandas / OpenPyXL\nCSV and Excel reports]
```

The FastAPI service serves the built single-page React application and `/api` from one listener. JWT authentication identifies the role; route dependencies enforce actions, while the Accountant/Auditor role can only read/export. Posted inventory changes create stock-ledger rows with source documents and audit-log entries.

## ER diagram

```mermaid
erDiagram
  ROLES ||--o{ USERS : grants
  USERS ||--o{ ORDERS : places
  USERS ||--o{ AUDIT_LOGS : performs
  CUSTOMERS ||--o{ ORDERS : receives
  PRODUCTS ||--o{ ORDERS : ordered
  PRODUCTS ||--o{ BOM_ITEMS : defined_by
  MATERIALS ||--o{ BOM_ITEMS : consumed_as
  SUPPLIERS ||--o{ PURCHASES : supplies
  PURCHASES ||--o{ PURCHASE_ITEMS : contains
  MATERIALS ||--o{ PURCHASE_ITEMS : purchased
  PRODUCTS ||--o{ PRODUCTION_RUNS : produced
  MATERIALS ||--o{ STOCK_MOVEMENTS : tracked
  PRODUCTS ||--o{ STOCK_MOVEMENTS : tracked
  ORDERS ||--o| INVOICES : billed_by
  INVOICES ||--o{ PAYMENTS : settled_by
```

Tables in the initial schema: roles, users, customers, suppliers, products, materials (raw/packaging), BOM items, purchases/items, production runs, stock movements, orders, invoices, payments, expenses and audit logs. Money columns are integer paisa; quantities use fixed-precision Decimal-backed database columns. Source movement documents, unique references and foreign keys preserve traceability.
