# Eight-minute SmartFactory demo script

**0:00–0:40 — Introduction.** Introduce SmartFactory as an order-to-audit operations workspace for a small Tamil Nadu packaged-food manufacturer. Explain that the demonstration uses the Murukku 200 g product, a defined bill of materials and source-referenced stock movements.

**0:40–1:30 — Login and dashboard.** Sign in as Admin. Show the dashboard, sales and production overview, operational alerts, recent orders and inventory health. Point out the reporting period and the navigation sections. Explain that access and available actions depend on the signed-in role.

**1:30–2:10 — Mobile salesman experience.** Open the application in a mobile-sized browser viewport and sign in as Salesman A. Show the mobile navigation and sales-order workflow. Explain how a salesperson can submit an order for a customer and product. Sign out when finished.

**2:10–3:10 — Production and BOM.** Sign back in as Admin and open Production. Show the Murukku 200 g BOM: 40 kg flour, 10 L cooking oil, 1.2 kg spice mix, 200 pouches and 10 cartons per standard batch. Explain weighted-average material valuation and the planned-versus-actual consumption chart.

**3:10–4:00 — Production results and inventory.** Show the existing benchmark results: 188 good packets from 200 expected, a −6% yield variance and +5% oil consumption variance. Explain the six damaged pouches and QC quarantine. Open Inventory and show on-hand versus available quantities, raw materials, packaging and source-referenced stock movements. Do not click Run benchmark or Re-run benchmark: the benchmark data is already loaded.

**4:00–5:10 — Sales orders and GST.** Open Sales orders. Show the Retailer A order for 150 packets and its completed workflow. Explain the admin approval, invoice generation and dispatch actions. Show the invoice figures: ₹7,500 taxable value, ₹187.50 CGST, ₹187.50 SGST and ₹7,875 total. Point out the separate Distributor B order for 120 packets and its 32-packet stock-shortage warning.

**5:10–6:00 — Billing and collection.** Open GST billing. Show the invoice, outstanding balance and payment history reflected in the billing summary. Point out the PDF download and Record payment controls. The seeded demonstration already includes a ₹4,000 receipt against the Retailer A invoice, leaving ₹3,875 outstanding. Do not submit the payment again.

**6:00–7:00 — Reports.** Open Reports and show the available operational and finance report cards, including GST summary, production, material ledger and receivables. Point out the CSV, Excel and PDF export options. Demonstrate only an export that has been tested successfully; do not claim that every report-format combination has been verified.

**7:00–8:00 — Technical close.** Open the API documentation at `/docs` and show the health endpoint. Mention FastAPI, React, SQLAlchemy and the database configuration. State that the automated test suite passes (5 tests). Close by explaining that real commercial deployment still requires validation of tax master data, security and tenant policies, backups, and applicable invoice and credit-note requirements.
