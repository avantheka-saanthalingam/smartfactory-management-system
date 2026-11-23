# Eight-minute SmartFactory demo script

**0:00–0:40 — Context.** Introduce SmartFactory as an order-to-audit operations desk for a small Tamil Nadu packaged-food unit. The demonstration starts with a seeded Murukku 200 g recipe and exact assignment opening stocks. Explain that every stock change is a source-referenced ledger movement.

**0:40–1:20 — Roles and overview.** Sign in with the Admin demo account. Point out net sales, open orders, finished goods and receivables. Switch roles using logout and the quick role selector to show that Salesman, Supervisor, Owner and Auditor have role-specific actions.

**1:20–2:20 — BOM and costing.** Open Production. Walk through 40 kg flour, 10 L oil, 1.2 kg spice, 200 pouches and 10 cartons per 200-packet batch. Explain the starting ₹42/kg flour rate and the weighted-average method after purchasing at ₹45/kg.

**2:20–3:30 — Benchmark production.** Click Run benchmark. Review 188 good packets from 200 expected, 6% yield variance, +5% oil issue variance and the >3% warning. Explain that the six damaged pouches are returned to the ledger in QC quarantine to match the assignment's 306 total pouch balance; 300 remain available for production. Check flour 120 kg, oil 19.5 L, spice 3.8 kg, cartons 21, finished goods 238 before dispatch and 88 after dispatch.

**3:30–4:30 — Sales and GST.** Open Sales orders and show the 150-packet Retailer A Tamil Nadu order. Generate or view its financial-year invoice. Explain ₹7,500 taxable value, ₹187.50 CGST, ₹187.50 SGST and ₹7,875 total. The built-in scenario dispatches this order and creates a second 120-packet Karnataka order with a 32-packet shortage alert.

**4:30–5:10 — Collection.** Open GST billing and show the ₹4,000 receipt against Retailer A's invoice, leaving ₹3,875 outstanding. Download the invoice PDF.

**5:10–6:10 — Inventory and traceability.** Open Inventory and point out raw/packaging separation, available versus QC-quarantined stock, source references, purchase/production/dispatch movements and adjustment controls. Emphasize transactional rollback on failed production/dispatch.

**6:10–7:10 — Reports.** Open Monthly reports. Export a GST summary, production report, material ledger and receivables aging to CSV, Excel or PDF. Explain the integer-paisa storage and Decimal quantity handling.

**7:10–8:00 — Close.** Show Swagger at `/docs`, mention automated tests and SQLite-to-PostgreSQL URL migration, and state current production-readiness boundaries: validate real tax master data, tenant/security policy, backups and live invoice/credit-note regulations before commercial deployment.
