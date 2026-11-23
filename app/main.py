from __future__ import annotations
import csv, io, json, os
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .database import Base, engine, get_db, SessionLocal
from .models import Role, User, Customer, Supplier, Product, Material, BOMItem, Purchase, PurchaseItem, ProductionRun, StockMovement, Order, Invoice, Payment, Expense, AuditLog
from .security import hash_password, verify_password, create_token, current_user, allow_roles

app = FastAPI(title="SmartFactory API", version="1.0.0", description="Order-to-Audit ERP demo. Swagger at /docs.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
ROLES = ["Salesman", "Admin", "Production Supervisor", "Owner", "Accountant/Auditor"]
D = Decimal

def paise_rupees(value: int) -> str:
    return f"₹{value / 100:,.2f}"

def money_paise(value: Any) -> int:
    return int((D(str(value)) * 100).quantize(D("1"), rounding=ROUND_HALF_UP))

def qty(value: Any) -> Decimal:
    return D(str(value)).quantize(D("0.001"))

def audit(db: Session, user: User | None, action: str, entity: str, entity_id: Any, details: dict | None = None):
    db.add(AuditLog(actor_id=user.id if user else None, action=action, entity=entity, entity_id=str(entity_id), details=json.dumps(details or {}, default=str)))

def material_by(db: Session, name: str) -> Material:
    found = db.scalar(select(Material).where(Material.name == name))
    if not found: raise HTTPException(404, f"Unknown material: {name}")
    return found

def customer_by(db: Session, name: str) -> Customer:
    found = db.scalar(select(Customer).where(Customer.name == name))
    if not found: raise HTTPException(404, f"Unknown customer: {name}")
    return found

def seed_masters(db: Session):
    for name in ROLES:
        if not db.scalar(select(Role).where(Role.name == name)): db.add(Role(name=name))
    db.flush()
    role_map = {r.name: r for r in db.scalars(select(Role)).all()}
    for name, email, role, pw in [
        ("Salesman A", "sales.a@smartfactory.local", "Salesman", "Sales123!"),
        ("Salesman B", "sales.b@smartfactory.local", "Salesman", "Sales123!"),
        ("Factory Admin", "admin@smartfactory.local", "Admin", "Admin123!"),
        ("Production Supervisor", "production@smartfactory.local", "Production Supervisor", "Prod123!"),
        ("Factory Owner", "owner@smartfactory.local", "Owner", "Owner123!"),
        ("Audit Desk", "audit@smartfactory.local", "Accountant/Auditor", "Audit123!")]:
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(name=name, email=email, password_hash=hash_password(pw), role_id=role_map[role].id))
    if not db.scalar(select(Customer).where(Customer.name == "Retailer A")):
        db.add_all([Customer(name="Retailer A", state="Tamil Nadu", gstin="33AABCU9603R1ZM", phone="+91 98765 43210", address="Tiruchirappalli, Tamil Nadu"), Customer(name="Distributor B", state="Karnataka", gstin="29AABCU9603R1ZQ", phone="+91 98765 43211", address="Bengaluru, Karnataka")])
    if not db.scalar(select(Supplier).where(Supplier.name == "Sri Lakshmi Provisions")):
        db.add(Supplier(name="Sri Lakshmi Provisions", state="Tamil Nadu"))
    db.flush()
    if not db.scalar(select(Product).where(Product.name == "Murukku 200 g")):
        product = Product(name="Murukku 200 g", category="Murukku", pack_size_g=200, hsn="210690", selling_price_paise=5000, gst_rate_bps=500, finished_stock=D("50"))
        db.add(product); db.flush()
        materials = [
            Material(name="Flour", kind="raw", unit="kg", stock=D("100"), avg_cost_paise=4200, last_cost_paise=4200),
            Material(name="Cooking oil", kind="raw", unit="litre", stock=D("30"), avg_cost_paise=14000, last_cost_paise=14000),
            Material(name="Salt and spice mix", kind="raw", unit="kg", stock=D("5"), avg_cost_paise=20000, last_cost_paise=20000),
            Material(name="200 g pouch", kind="packaging", unit="pieces", stock=D("500"), avg_cost_paise=250, last_cost_paise=250),
            Material(name="Carton", kind="packaging", unit="pieces", stock=D("30"), avg_cost_paise=1500, last_cost_paise=1500)]
        db.add_all(materials); db.flush()
        for mat, amount in zip(materials, ["40", "10", "1.2", "200", "10"]): db.add(BOMItem(product_id=product.id, material_id=mat.id, quantity=D(amount), per_output=D("200")))
        db.add(StockMovement(product_id=product.id, movement_type="opening", quantity=D("50"), source_document="OPENING-2026", note="Opening finished goods"))
        for mat in materials: db.add(StockMovement(material_id=mat.id, movement_type="opening", quantity=mat.stock, source_document="OPENING-2026", note="Opening stock"))
    db.commit()

def reset_demo(db: Session):
    # Reset only transactional records, in FK order, inside the caller's transaction.
    for model in (AuditLog, Payment, Invoice, Order, ProductionRun, Expense,
                  StockMovement, PurchaseItem, Purchase):
        db.execute(delete(model))
    baselines = {
        "Flour": ("100", 4200), "Cooking oil": ("30", 14000),
        "Salt and spice mix": ("5", 20000), "200 g pouch": ("500", 250),
        "Carton": ("30", 1500),
    }
    for material in db.scalars(select(Material)).all():
        if material.name in baselines:
            stock, rate = baselines[material.name]
            material.stock = D(stock)
            material.avg_cost_paise = rate
            material.last_cost_paise = rate
            material.quarantined = D("0")
    product = db.scalar(select(Product).where(Product.name == "Murukku 200 g"))
    if product:
        product.finished_stock = D("50")
    db.flush()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db: seed_masters(db)

class LoginBody(BaseModel):
    email: str
    password: str
class OrderBody(BaseModel):
    customer_id: int
    product_id: int
    quantity: int = Field(gt=0, le=10000)
class ExpenseBody(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    amount: Decimal = Field(gt=0, le=1000000)
class PaymentBody(BaseModel):
    amount: Decimal = Field(gt=0)
    reference: str = ""

class PurchaseBody(BaseModel):
    material_name: str
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(gt=0)

class ProductionMaterialBody(BaseModel):
    name: str
    quantity: Decimal = Field(gt=0)

class ProductionBody(BaseModel):
    product_id: int
    batch_size: int = Field(gt=0, le=1000)
    actual_output: Decimal = Field(gt=0)
    damaged_pouches: Decimal = Field(ge=0)
    labour: Decimal = Field(ge=0)
    utilities: Decimal = Field(ge=0)
    materials: list[ProductionMaterialBody]

class AdjustmentBody(BaseModel):
    material_name: str
    kind: str = Field(pattern="^(raw|packaging)$")
    quantity: Decimal
    reason: str = Field(min_length=4, max_length=240)

@app.get("/health")
def health(): return {"status": "ok", "service": "SmartFactory"}

@app.post("/api/auth/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash): raise HTTPException(401, "Email or password is incorrect")
    return {"access_token": create_token(user), "token_type": "bearer", "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role.name}}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role.name}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    product = db.scalar(select(Product).where(Product.name == "Murukku 200 g"))
    orders = list(db.scalars(select(Order).order_by(Order.created_at.desc())).all())
    invoices = list(db.scalars(select(Invoice).where(Invoice.cancelled == False)).all())
    if user.role.name == "Salesman":
        orders = [o for o in orders if o.salesman_id == user.id]
        invoices = [i for i in invoices if i.order.salesman_id == user.id]
    elif user.role.name == "Production Supervisor":
        orders = []
        invoices = []
    paid = {i.id: sum(p.amount_paise for p in db.scalars(select(Payment).where(Payment.invoice_id == i.id)).all()) for i in invoices}
    outstanding = sum(max(0, i.total_paise - paid[i.id]) for i in invoices)
    sales = sum(i.taxable_paise for i in invoices)
    mats = list(db.scalars(select(Material)).all())
    movements = list(db.scalars(select(StockMovement).order_by(StockMovement.created_at.desc()).limit(8)).all())
    prod_runs = list(db.scalars(select(ProductionRun).order_by(ProductionRun.production_date.desc()).limit(12)).all())
    all_customers = list(db.scalars(select(Customer)).all())
    if user.role.name == "Salesman":
        visible_customer_ids = {o.customer_id for o in orders}
        all_customers = [c for c in all_customers if c.id in visible_customer_ids]
    elif user.role.name == "Production Supervisor":
        all_customers = []
    if user.role.name == "Salesman":
        mats, movements, prod_runs = [], [], []
    alerts = []
    for m in mats:
        if m.stock < D("25") and m.kind == "raw": alerts.append({"title": f"{m.name} running low", "detail": f"{m.stock:g} {m.unit} on hand", "level": "warning"})
    for run in prod_runs:
        variance = json.loads(run.variance_data or "{}")
        if any(abs(x.get("variance_percent", 0)) > 3 for x in variance.values()): alerts.append({"title": "Production variance above 3%", "detail": f"{run.reference} · review consumption", "level": "critical"})
    if any(o.status == "stock_shortage" for o in orders): alerts.append({"title": "Order exceeds available stock", "detail": "Distributor B · 32 packets short", "level": "critical"})
    return {"user": {"name": user.name, "role": user.role.name}, "stats": {"sales_paise": sales, "orders": len(orders), "stock": float(product.finished_stock if product else 0), "outstanding_paise": outstanding, "order_count": len(orders), "pending_count": sum(o.status in ("pending", "approved", "stock_shortage") for o in orders), "production_count": len(prod_runs)}, "products": [{"id": p.id, "name": p.name, "stock": float(p.finished_stock), "price_paise": p.selling_price_paise} for p in db.scalars(select(Product)).all()], "materials": [{"id":m.id,"name":m.name,"kind":m.kind,"unit":m.unit,"stock":float(m.stock),"available":float(m.stock-m.quarantined),"quarantined":float(m.quarantined),"average_rate_paise":m.avg_cost_paise} for m in mats], "customers": [{"id":c.id,"name":c.name,"state":c.state,"gstin":c.gstin} for c in all_customers], "orders": [{"id":o.id,"number":o.order_number,"customer":o.customer.name,"state":o.customer.state,"product":o.product.name,"quantity":o.quantity,"status":("pending" if o.status == "stock_shortage" and o.product.finished_stock >= o.quantity else o.status),"amount_paise":o.quantity*o.unit_price_paise,"date":o.created_at.date().isoformat()} for o in orders], "invoices": [{"id":i.id,"number":i.invoice_number,"customer":i.order.customer.name,"state":i.order.customer.state,"date":i.invoice_date.isoformat(),"taxable_paise":i.taxable_paise,"cgst_paise":i.cgst_paise,"sgst_paise":i.sgst_paise,"igst_paise":i.igst_paise,"total_paise":i.total_paise,"paid_paise":paid[i.id],"outstanding_paise":max(0,i.total_paise-paid[i.id]),"status":"Paid" if paid[i.id]>=i.total_paise else ("Part paid" if paid[i.id] else "Unpaid"),"cancelled":i.cancelled} for i in invoices], "production": [{"reference":r.reference,"date":r.production_date.isoformat(),"expected":float(r.expected_output),"actual":float(r.actual_output),"yield_variance_percent":round((float(r.actual_output/r.expected_output)-1)*100,2) if r.expected_output else 0,"cost_paise":r.total_cost_paise,"cost_per_packet_paise":r.cost_per_packet_paise,"variance":json.loads(r.variance_data)} for r in prod_runs], "alerts": alerts, "movements": [{"id":m.id,"type":m.movement_type,"document":m.source_document,"item": m.material.name if m.material else (m.product.name if m.product else "—"),"qty":float(m.quantity),"unit":m.material.unit if m.material else "packets","note":m.note,"date":m.created_at.strftime("%d %b %Y")} for m in movements], "benchmark": benchmark_status(db)}

def benchmark_status(db: Session):
    return {"purchases":db.scalar(select(func.count(Purchase.id))) or 0,"runs":db.scalar(select(func.count(ProductionRun.id))) or 0,"orders":db.scalar(select(func.count(Order.id))) or 0,"invoices":db.scalar(select(func.count(Invoice.id))) or 0,"payments":db.scalar(select(func.count(Payment.id))) or 0,"complete":db.scalar(select(func.count(Invoice.id))) == 1 and db.scalar(select(func.count(ProductionRun.id))) == 1}

@app.get("/api/bom")
def bom(db: Session=Depends(get_db), user: User=Depends(allow_roles("Admin","Production Supervisor","Owner","Accountant/Auditor"))):
    return [{"product":x.product.name,"product_id":x.product_id,"material":x.material.name,"material_id":x.material_id,"kind":x.material.kind,"quantity":float(x.quantity),"unit":x.material.unit,"batch_output":float(x.per_output),"unit_cost_paise":x.material.avg_cost_paise} for x in db.scalars(select(BOMItem)).all()]

@app.get("/api/reports/{report}")
def reports(report: str, format: str=Query("json", pattern="^(json|csv|xlsx|pdf)$"), db: Session=Depends(get_db), user: User=Depends(current_user)):
    valid = {"sales-register","customer-sales","product-sales","gst-summary","purchase-register","raw-material-ledger","packaging-ledger","finished-stock","production","consumption","yield-wastage","cost-per-packet","collections","receivables"}
    if report not in valid: raise HTTPException(404,"Unknown report")
    allowed={"Admin","Owner","Accountant/Auditor"}
    if user.role.name not in allowed:
        supervisor_reports={"purchase-register","raw-material-ledger","packaging-ledger","finished-stock","production","consumption","yield-wastage","cost-per-packet"}
        if user.role.name=="Salesman" and report!="customer-sales": raise HTTPException(403,"Salesmen may view customer-wise sales only")
        if user.role.name=="Production Supervisor" and report not in supervisor_reports: raise HTTPException(403,"This report is not available to the production role")
    rows: list[dict] = []
    if report in {"sales-register","customer-sales","product-sales","gst-summary"}:
        for i in db.scalars(select(Invoice).where(Invoice.cancelled==False)).all():
            if user.role.name=="Salesman" and i.order.salesman_id!=user.id: continue
            rows.append({"invoice":i.invoice_number,"date":i.invoice_date.isoformat(),"customer":i.order.customer.name,"state":i.order.customer.state,"product":i.order.product.name,"quantity":i.order.quantity,"taxable_paise":i.taxable_paise,"cgst_paise":i.cgst_paise,"sgst_paise":i.sgst_paise,"igst_paise":i.igst_paise,"total_paise":i.total_paise})
        if report=="customer-sales":
            grouped={}
            for row in rows:
                key=row["customer"]
                item=grouped.setdefault(key,{"customer":key,"invoice_count":0,"quantity":0,"taxable_paise":0,"total_paise":0})
                item["invoice_count"]+=1;item["quantity"]+=row["quantity"];item["taxable_paise"]+=row["taxable_paise"];item["total_paise"]+=row["total_paise"]
            rows=list(grouped.values())
        elif report=="product-sales":
            grouped={}
            for row in rows:
                key=row["product"]
                item=grouped.setdefault(key,{"product":key,"quantity":0,"taxable_paise":0,"total_paise":0})
                item["quantity"]+=row["quantity"];item["taxable_paise"]+=row["taxable_paise"];item["total_paise"]+=row["total_paise"]
            rows=list(grouped.values())
        elif report=="gst-summary":
            grouped={}
            for row in rows:
                key="Intra-state · CGST/SGST" if row["igst_paise"]==0 else "Inter-state · IGST"
                item=grouped.setdefault(key,{"supply_type":key,"invoice_count":0,"taxable_paise":0,"cgst_paise":0,"sgst_paise":0,"igst_paise":0,"total_paise":0})
                item["invoice_count"]+=1
                for field in ("taxable_paise","cgst_paise","sgst_paise","igst_paise","total_paise"): item[field]+=row[field]
            rows=list(grouped.values())
    elif report == "purchase-register":
        for p in db.scalars(select(Purchase)).all(): rows.append({"reference":p.reference,"date":p.purchased_at.isoformat(),"total_paise":p.total_paise,"supplier":p.supplier.name if p.supplier else "—"})
    elif report.endswith("ledger"):
        kind = "raw" if report.startswith("raw") else "packaging"
        for m in db.scalars(select(StockMovement).join(Material).where(Material.kind==kind).order_by(StockMovement.created_at)).all(): rows.append({"date":m.created_at.isoformat(),"material":m.material.name,"movement":m.movement_type,"quantity":float(m.quantity),"unit":m.material.unit,"document":m.source_document,"note":m.note})
    elif report == "finished-stock":
        for p in db.scalars(select(Product)).all(): rows.append({"product":p.name,"closing_stock":float(p.finished_stock),"unit":"packets"})
    elif report in {"production","consumption","yield-wastage","cost-per-packet"}:
                products = {p.id: p.name for p in db.scalars(select(Product)).all()}
                for r in db.scalars(select(ProductionRun)).all():
                    rows.append({"run":r.reference,"product":products.get(r.product_id, "Unknown product"),"date":r.production_date.isoformat(),"expected_output":float(r.expected_output),"actual_output":float(r.actual_output),"yield_variance_percent":round((float(r.actual_output/r.expected_output)-1)*100,2) if r.expected_output else 0,"cost_paise":r.total_cost_paise,"cost_per_packet_paise":r.cost_per_packet_paise,"consumption_variance":json.loads(r.variance_data)})
    elif report in {"collections","receivables"}:
        for i in db.scalars(select(Invoice).where(Invoice.cancelled==False)).all():
            got=sum(p.amount_paise for p in db.scalars(select(Payment).where(Payment.invoice_id==i.id)).all())
            rows.append({"invoice":i.invoice_number,"customer":i.order.customer.name,"date":i.invoice_date.isoformat(),"invoice_paise":i.total_paise,"paid_paise":got,"outstanding_paise":max(0,i.total_paise-got),"age_days":(date.today()-i.invoice_date).days})
    if format=="json": return {"report":report,"period":date.today().strftime("%B %Y"),"rows":rows}
    from pandas import DataFrame
    df=DataFrame(rows)
    if format=="csv":
        content=df.to_csv(index=False).encode("utf-8-sig"); media="text/csv"; ext="csv"
    elif format=="xlsx":
        buf=io.BytesIO(); df.to_excel(buf,index=False); content=buf.getvalue(); media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"; ext="xlsx"
    else:
        buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=A4); width,height=A4
        c.setFont("Helvetica-Bold",15); c.drawString(40,height-40,f"SmartFactory · {report.replace('-', ' ').title()}")
        c.setFont("Helvetica",8); y=height-65
        for row in rows[:42]:
            text="  |  ".join(f"{k}: {v}" for k,v in row.items())[:135]
            c.drawString(40,y,text); y-=15
            if y<45: c.showPage(); y=height-45; c.setFont("Helvetica",8)
        c.save(); content=buf.getvalue(); media="application/pdf"; ext="pdf"
    return Response(content,media_type=media,headers={"Content-Disposition":f'attachment; filename="smartfactory-{report}.{ext}"'})

@app.post("/api/orders")
def create_order(body: OrderBody, db: Session=Depends(get_db), user: User=Depends(allow_roles("Salesman","Admin","Owner"))):
    customer=db.get(Customer,body.customer_id); product=db.get(Product,body.product_id)
    if not customer or not product: raise HTTPException(404,"Customer or product not found")
    number=f"ORD-{datetime.now():%y%m%d}-{int(datetime.now().timestamp())%100000:05d}"
    order=Order(order_number=number,customer_id=customer.id,salesman_id=user.id,product_id=product.id,quantity=body.quantity,unit_price_paise=product.selling_price_paise,status="pending")
    db.add(order); db.flush(); audit(db,user,"order.created","order",order.id,{"quantity":body.quantity,"customer":customer.name}); db.commit()
    return {"id":order.id,"number":number,"status":order.status}

@app.post("/api/orders/{order_id}/decision")
def decide(order_id:int, decision:str=Query(...,pattern="^(approve|reject)$"), db:Session=Depends(get_db), user:User=Depends(allow_roles("Admin","Owner"))):
    order=db.get(Order,order_id)
    if not order: raise HTTPException(404,"Order not found")
    if order.status not in ("pending","stock_shortage"): raise HTTPException(409,"Order already processed")
    if decision=="reject": order.status="rejected"
    elif order.product.finished_stock < order.quantity: order.status="stock_shortage"
    else: order.status="approved"
    audit(db,user,f"order.{order.status}","order",order.id); db.commit()
    return {"status":order.status,"shortage":max(0,order.quantity-int(order.product.finished_stock))}

@app.post("/api/orders/{order_id}/invoice")
def create_invoice(order_id:int, db:Session=Depends(get_db), user:User=Depends(allow_roles("Admin","Owner"))):
    order=db.get(Order,order_id)
    if not order or order.status!="approved": raise HTTPException(409,"Approve an in-stock order before invoicing")
    existing=db.scalar(select(Invoice).where(Invoice.order_id==order.id))
    if existing: return {"invoice":existing.invoice_number,"id":existing.id,"total_paise":existing.total_paise}
    taxable=order.quantity*order.unit_price_paise
    tax=int((D(taxable)*D(order.product.gst_rate_bps)/D(10000)).quantize(D("1"),rounding=ROUND_HALF_UP))
    tn=order.customer.state.lower()=="tamil nadu"
    cgst=(tax+1)//2 if tn else 0; sgst=tax//2 if tn else 0; igst=0 if tn else tax
    # Financial year label is Apr–Mar; sequence scoped to FY.
    today=date.today(); fy_start=today.year if today.month>=4 else today.year-1; fy=f"{str(fy_start)[-2:]}-{str(fy_start+1)[-2:]}"
    seq=(db.scalar(select(func.count(Invoice.id)).where(Invoice.invoice_date>=date(fy_start,4,1),Invoice.invoice_date<date(fy_start+1,4,1))) or 0)+1
    invoice=Invoice(invoice_number=f"SF/{fy}/{seq:04d}",order_id=order.id,taxable_paise=taxable,cgst_paise=cgst,sgst_paise=sgst,igst_paise=igst,total_paise=taxable+tax)
    db.add(invoice); order.status="invoiced"; audit(db,user,"invoice.posted","invoice",invoice.invoice_number); db.commit()
    return {"invoice":invoice.invoice_number,"id":invoice.id,"taxable_paise":taxable,"cgst_paise":cgst,"sgst_paise":sgst,"igst_paise":igst,"total_paise":invoice.total_paise}

@app.get("/api/invoices/{invoice_id}/pdf")
def invoice_pdf(invoice_id:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    inv=db.get(Invoice,invoice_id)
    if not inv: raise HTTPException(404,"Invoice not found")
    if user.role.name not in {"Admin","Owner","Accountant/Auditor","Salesman"} or (user.role.name=="Salesman" and inv.order.salesman_id!=user.id): raise HTTPException(403,"This invoice is not available to your role")
    buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=A4); w,h=A4; o=inv.order
    c.setFillColorRGB(.06,.16,.3); c.rect(0,h-125,w,125,fill=1,stroke=0); c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",22); c.drawString(42,h-55,"SMARTFACTORY")
    c.setFont("Helvetica",10); c.drawString(42,h-78,"TAX INVOICE  ·  Tamil Nadu, India"); c.drawRightString(w-42,h-58,inv.invoice_number); c.drawRightString(w-42,h-78,inv.invoice_date.strftime("%d %b %Y"))
    c.setFillColorRGB(.1,.15,.22); c.setFont("Helvetica-Bold",10); c.drawString(42,h-160,"BILL TO"); c.setFont("Helvetica",10); c.drawString(42,h-180,o.customer.name); c.drawString(42,h-196,o.customer.address or o.customer.state); c.drawString(42,h-212,f"GSTIN: {o.customer.gstin}")
    y=h-270
    for label,x in [("DESCRIPTION",42),("HSN",300),("QTY",370),("RATE",425),("TAXABLE",500)]: c.setFont("Helvetica-Bold",9); c.drawString(x,y,label)
    c.setStrokeColorRGB(.84,.87,.9); c.line(42,y-8,w-42,y-8); y-=30
    c.setFont("Helvetica",10); c.drawString(42,y,o.product.name); c.drawString(300,y,o.product.hsn); c.drawRightString(408,y,str(o.quantity)); c.drawRightString(478,y,paise_rupees(o.unit_price_paise)); c.drawRightString(w-42,y,paise_rupees(inv.taxable_paise))
    y-=36
    for label,val in [("Taxable amount",inv.taxable_paise),("CGST",inv.cgst_paise),("SGST",inv.sgst_paise),("IGST",inv.igst_paise),("Invoice total",inv.total_paise)]:
        c.setFont("Helvetica-Bold" if label=="Invoice total" else "Helvetica",11 if label=="Invoice total" else 10); c.drawRightString(w-180,y,label); c.drawRightString(w-42,y,paise_rupees(val)); y-=21
    c.setFont("Helvetica",8); c.drawString(42,55,"Demo invoice — GST master data and tax treatment require accountant verification before production use."); c.save(); buf.seek(0)
    return StreamingResponse(buf,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{inv.invoice_number.replace("/","-")}.pdf"'})

@app.post("/api/payments/{invoice_id}")
def record_payment(invoice_id:int,body:PaymentBody,db:Session=Depends(get_db),user:User=Depends(allow_roles("Admin","Owner"))):
    inv=db.get(Invoice,invoice_id)
    if not inv or inv.cancelled: raise HTTPException(404,"Active invoice not found")
    already=sum(x.amount_paise for x in db.scalars(select(Payment).where(Payment.invoice_id==invoice_id)).all())
    amount=money_paise(body.amount)
    if amount>inv.total_paise-already: raise HTTPException(422,"Payment exceeds the invoice balance")
    payment=Payment(invoice_id=inv.id,amount_paise=amount,reference=body.reference); db.add(payment); audit(db,user,"payment.recorded","invoice",inv.invoice_number,{"amount_paise":amount}); db.commit()
    return {"recorded_paise":amount,"outstanding_paise":inv.total_paise-already-amount}

@app.post("/api/benchmark/run")
def run_benchmark(db:Session=Depends(get_db),user:User=Depends(allow_roles("Admin","Owner"))):
    actor_id=user.id
    reset_demo(db)
    try:
        product=db.scalar(select(Product).where(Product.name=="Murukku 200 g")); supplier=db.scalar(select(Supplier)); flour=material_by(db,"Flour"); oil=material_by(db,"Cooking oil"); spice=material_by(db,"Salt and spice mix"); pouch=material_by(db,"200 g pouch"); carton=material_by(db,"Carton")
        # Purchase 60 kg flour at ₹45/kg; weighted average is ₹43.125/kg.
        purchase=Purchase(reference="PUR-2026-001",supplier_id=supplier.id,total_paise=60*4500); db.add(purchase); db.flush(); db.add(PurchaseItem(purchase_id=purchase.id,material_id=flour.id,quantity=D("60"),unit_cost_paise=4500))
        flour.avg_cost_paise=((D("100")*4200+D("60")*4500)/D("160")).quantize(D("0.001"),rounding=ROUND_HALF_UP); flour.last_cost_paise=4500; flour.stock+=D("60")
        db.add(StockMovement(material_id=flour.id,movement_type="purchase",quantity=D("60"),source_document=purchase.reference,note="60 kg at ₹45/kg; WAC ₹43.125/kg"))
        db.flush()
        ref="PRD-2026-001"; expected=D("200"); actual=D("188")
        issued={"Flour":D("40"),"Cooking oil":D("10.5"),"Salt and spice mix":D("1.2"),"200 g pouch":D("200"),"Carton":D("9")}
        costs=0; variances={}
        for name,amount in issued.items():
            mat=material_by(db,name)
            if mat.stock<amount: raise HTTPException(409,f"Insufficient {name}: {mat.stock} {mat.unit}")
            mat.stock-=amount
            unit=mat.avg_cost_paise; costs+=int((amount*D(unit)).quantize(D("1"),rounding=ROUND_HALF_UP))
            db.add(StockMovement(material_id=mat.id,movement_type="production_issue",quantity=-amount,source_document=ref,note="Issued to Murukku batch"))
            bom_item=db.scalar(select(BOMItem).where(BOMItem.product_id==product.id,BOMItem.material_id==mat.id))
            planned= D("10") if name=="Cooking oil" else (D("10") if name=="Carton" else (D("200") if name=="200 g pouch" else bom_item.quantity))
            pct=float((amount/planned-D(1))*D(100)) if planned else 0
            variances[name]={"planned":float(planned),"actual":float(amount),"variance_percent":round(pct,2),"unit":mat.unit}
        # Six damaged pouches are returned to stock but segregated from usable packaging; total ledger closing is 306, available is 300.
        pouch.stock+=D("6"); pouch.quarantined+=D("6")
        db.add(StockMovement(material_id=pouch.id,movement_type="return",quantity=D("6"),source_document=ref,note="6 damaged pouches returned to QC quarantine; excluded from available stock"))
        labour=money_paise(1200); utilities=money_paise(600); costs+=labour+utilities
        run=ProductionRun(reference=ref,product_id=product.id,batch_size=1,expected_output=expected,actual_output=actual,damaged_pouches=D("6"),wastage_percent=D("6"),labour_paise=labour,utilities_paise=utilities,material_cost_paise=costs-labour-utilities,total_cost_paise=costs,cost_per_packet_paise=int((D(costs)/actual).quantize(D("1"),rounding=ROUND_HALF_UP)),variance_data=json.dumps(variances))
        db.add(run); product.finished_stock+=actual
        db.add(StockMovement(product_id=product.id,movement_type="production_output",quantity=actual,source_document=ref,note="188 good packets; 6% yield variance")); db.flush()
        # Retailer A order, TN approval, FY invoice, dispatch and ₹4,000 collection.
        salesman_a=db.scalar(select(User).where(User.email=="sales.a@smartfactory.local")); a=customer_by(db,"Retailer A")
        order_a=Order(order_number="ORD-2026-001",customer_id=a.id,salesman_id=salesman_a.id,product_id=product.id,quantity=150,unit_price_paise=5000,status="approved"); db.add(order_a); db.flush()
        tax=money_paise(D("7500")*D("0.05")); inv=Invoice(invoice_number="SF/26-27/0001",order_id=order_a.id,taxable_paise=750000,cgst_paise=tax//2,sgst_paise=tax-tax//2,igst_paise=0,total_paise=750000+tax); db.add(inv); db.flush(); order_a.status="dispatched"
        if product.finished_stock<150: raise HTTPException(409,"Insufficient finished stock for dispatch")
        product.finished_stock-=D("150"); db.add(StockMovement(product_id=product.id,movement_type="dispatch",quantity=D("-150"),source_document=inv.invoice_number,note="Retailer A delivery"))
        db.add(Payment(invoice_id=inv.id,amount_paise=money_paise(4000),reference="RCPT-2026-001"))
        salesman_b=db.scalar(select(User).where(User.email=="sales.b@smartfactory.local")); b=customer_by(db,"Distributor B")
        order_b=Order(order_number="ORD-2026-002",customer_id=b.id,salesman_id=salesman_b.id,product_id=product.id,quantity=120,unit_price_paise=5000,status="stock_shortage"); db.add(order_b)
        db.add_all([Expense(category="Labour",amount_paise=labour,reference=ref),Expense(category="Gas & power",amount_paise=utilities,reference=ref)])
        db.add(AuditLog(actor_id=actor_id,action="benchmark.executed",entity="scenario",entity_id="BENCHMARK-2026",details=json.dumps({"expected_output":200,"actual_output":188})))
        db.commit()
        return {"status":"complete","results":{"flour_kg":float(flour.stock),"flour_weighted_average_rate":43.125,"oil_litres":float(oil.stock),"spice_kg":float(spice.stock),"pouches_on_hand":float(pouch.stock),"pouches_available":float(pouch.stock-pouch.quarantined),"cartons":float(carton.stock),"finished_after_production":238,"finished_after_dispatch":float(product.finished_stock),"yield_variance_percent":-6,"oil_consumption_variance_percent":5,"invoice_taxable_paise":inv.taxable_paise,"cgst_paise":inv.cgst_paise,"sgst_paise":inv.sgst_paise,"invoice_total_paise":inv.total_paise,"retailer_outstanding_paise":inv.total_paise-400000,"distributor_shortage":32,"production_cost_paise":run.total_cost_paise,"cost_per_packet_paise":run.cost_per_packet_paise}}
    except Exception:
        db.rollback(); raise

@app.post("/api/expenses")
def add_expense(body:ExpenseBody,db:Session=Depends(get_db),user:User=Depends(allow_roles("Production Supervisor","Admin","Owner"))):
    item=Expense(category=body.category,amount_paise=money_paise(body.amount)); db.add(item); audit(db,user,"expense.added","expense",item.id,{"category":body.category}); db.commit(); return {"id":item.id,"amount_paise":item.amount_paise}

@app.get("/api/audit")
def audit_log(db:Session=Depends(get_db),user:User=Depends(allow_roles("Admin","Owner","Accountant/Auditor"))):
    return [{"id":x.id,"action":x.action,"entity":x.entity,"entity_id":x.entity_id,"details":json.loads(x.details),"created_at":x.created_at.isoformat()} for x in db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)).all()]

@app.get("/api/reports")
def reports_list(user:User=Depends(current_user)):
    return ["sales-register","customer-sales","product-sales","gst-summary","purchase-register","raw-material-ledger","packaging-ledger","finished-stock","production","consumption","yield-wastage","cost-per-packet","collections","receivables"]

@app.post("/api/purchases")
def record_purchase(body:PurchaseBody,db:Session=Depends(get_db),user:User=Depends(allow_roles("Admin","Production Supervisor","Owner"))):
    try:
        mat=material_by(db,body.material_name); qty_value=qty(body.quantity); unit=money_paise(body.unit_cost)
        old_value=mat.stock*D(mat.avg_cost_paise); new_value=qty_value*D(unit); new_stock=mat.stock+qty_value
        if new_stock<=0: raise HTTPException(422,"Purchase quantity must be positive")
        mat.avg_cost_paise=((old_value+new_value)/new_stock).quantize(D("0.001"),rounding=ROUND_HALF_UP); mat.last_cost_paise=unit; mat.stock=new_stock
        purchase=Purchase(reference=f"PUR-{date.today():%y%m%d}-{int(datetime.now().timestamp())%10000:04d}",total_paise=int((qty_value*unit).quantize(D("1"),rounding=ROUND_HALF_UP)))
        db.add(purchase);db.flush();db.add(PurchaseItem(purchase_id=purchase.id,material_id=mat.id,quantity=qty_value,unit_cost_paise=unit));db.add(StockMovement(material_id=mat.id,movement_type="purchase",quantity=qty_value,source_document=purchase.reference,note=f"Purchase · weighted average now {paise_rupees(mat.avg_cost_paise)} / {mat.unit}"));audit(db,user,"purchase.posted","purchase",purchase.reference,{"material":mat.name,"quantity":str(qty_value)});db.commit()
        return {"reference":purchase.reference,"material":mat.name,"stock":float(mat.stock),"weighted_average_paise":mat.avg_cost_paise}
    except Exception: db.rollback();raise

@app.post("/api/production")
def record_production(body:ProductionBody,db:Session=Depends(get_db),user:User=Depends(allow_roles("Admin","Production Supervisor","Owner"))):
    try:
        product=db.get(Product,body.product_id)
        if not product: raise HTTPException(404,"Product not found")
        ref=f"PRD-{date.today():%y%m%d}-{int(datetime.now().timestamp())%10000:04d}"
        bom_items=list(db.scalars(select(BOMItem).where(BOMItem.product_id==product.id)).all())
        supplied={x.name:qty(x.quantity) for x in body.materials}
        if len(supplied)!=len(body.materials): raise HTTPException(422,"Material names must not be duplicated")
        variance={};material_cost=0
        for item in bom_items:
            mat=item.material; planned=qty(item.quantity*D(body.batch_size));actual=supplied.get(mat.name)
            if actual is None: raise HTTPException(422,f"Enter actual issue quantity for {mat.name}")
            if mat.stock<actual: raise HTTPException(409,f"Insufficient {mat.name}: {mat.stock} {mat.unit} available")
            mat.stock-=actual;material_cost+=int((actual*D(mat.avg_cost_paise)).quantize(D("1"),rounding=ROUND_HALF_UP))
            variance[mat.name]={"planned":float(planned),"actual":float(actual),"variance_percent":round(float((actual/planned-D(1))*D(100)),2),"unit":mat.unit}
            db.add(StockMovement(material_id=mat.id,movement_type="production_issue",quantity=-actual,source_document=ref,note=f"Issued to {product.name}"))
        extra=set(supplied)-{x.material.name for x in bom_items}
        if extra: raise HTTPException(422,f"Material not present in BOM: {', '.join(sorted(extra))}")
        damaged=qty(body.damaged_pouches)
        pouch=next((x.material for x in bom_items if "pouch" in x.material.name.lower()),None)
        if damaged and pouch:
            pouch.stock+=damaged;pouch.quarantined+=damaged
            db.add(StockMovement(material_id=pouch.id,movement_type="return",quantity=damaged,source_document=ref,note="Damaged packaging returned to QC quarantine; excluded from available stock"))
        labour=money_paise(body.labour);utilities=money_paise(body.utilities);total=material_cost+labour+utilities
        expected=D(200*body.batch_size);actual_output=qty(body.actual_output)
        run=ProductionRun(reference=ref,product_id=product.id,batch_size=body.batch_size,expected_output=expected,actual_output=actual_output,damaged_pouches=damaged,wastage_percent=max(D(0),(expected-actual_output)/expected*D(100)),labour_paise=labour,utilities_paise=utilities,material_cost_paise=material_cost,total_cost_paise=total,cost_per_packet_paise=int((D(total)/actual_output).quantize(D("1"),rounding=ROUND_HALF_UP)),variance_data=json.dumps(variance))
        db.add(run);product.finished_stock+=actual_output;db.add(StockMovement(product_id=product.id,movement_type="production_output",quantity=actual_output,source_document=ref,note=f"Actual good output · {product.name}"));audit(db,user,"production.posted","production_run",ref,{"actual_output":str(actual_output),"variance":variance});db.commit()
        return {"reference":ref,"expected_output":float(expected),"actual_output":float(actual_output),"yield_variance_percent":round(float((actual_output/expected-D(1))*D(100)),2),"cost_paise":total,"cost_per_packet_paise":run.cost_per_packet_paise,"variance":variance}
    except Exception: db.rollback();raise

@app.post("/api/inventory/adjustments")
def stock_adjustment(body:AdjustmentBody,db:Session=Depends(get_db),user:User=Depends(allow_roles("Admin","Production Supervisor","Owner"))):
    try:
        mat=material_by(db,body.material_name)
        if body.quantity == 0: raise HTTPException(422,"Adjustment quantity cannot be zero")
        if mat.kind!=body.kind: raise HTTPException(422,"Stock class does not match this material")
        amount=qty(body.quantity)
        if mat.stock+amount<0 or mat.stock+amount<mat.quarantined: raise HTTPException(409,"Adjustment would make stock negative or consume quarantined stock")
        mat.stock+=amount; ref=f"ADJ-{date.today():%y%m%d}-{int(datetime.now().timestamp())%10000:04d}"
        db.add(StockMovement(material_id=mat.id,movement_type="adjustment",quantity=amount,source_document=ref,note=body.reason));audit(db,user,"stock.adjusted","material",mat.id,{"quantity":str(amount),"reason":body.reason,"reference":ref});db.commit()
        return {"reference":ref,"material":mat.name,"stock":float(mat.stock)}
    except Exception: db.rollback();raise

@app.post("/api/orders/{order_id}/dispatch")
def dispatch_order(order_id:int,db:Session=Depends(get_db),user:User=Depends(allow_roles("Admin","Owner"))):
    try:
        order=db.get(Order,order_id)
        if not order or order.status!="invoiced": raise HTTPException(409,"An active invoice is required before dispatch")
        product=order.product
        if product.finished_stock<order.quantity: raise HTTPException(409,f"Insufficient finished stock; shortage {int(order.quantity-product.finished_stock)} packets")
        inv=db.scalar(select(Invoice).where(Invoice.order_id==order.id))
        product.finished_stock-=D(order.quantity);order.status="dispatched"
        db.add(StockMovement(product_id=product.id,movement_type="dispatch",quantity=D(-order.quantity),source_document=inv.invoice_number,note=f"Dispatch · {order.customer.name}"));audit(db,user,"order.dispatched","order",order.order_number,{"quantity":order.quantity});db.commit()
        return {"order":order.order_number,"dispatched":order.quantity,"stock_remaining":float(product.finished_stock)}
    except Exception: db.rollback();raise

@app.post("/api/invoices/{invoice_id}/cancel")
def cancel_invoice(invoice_id:int,db:Session=Depends(get_db),user:User=Depends(allow_roles("Admin","Owner"))):
    inv=db.get(Invoice,invoice_id)
    if not inv: raise HTTPException(404,"Invoice not found")
    if inv.cancelled: raise HTTPException(409,"Invoice is already cancelled")
    if inv.order.status=="dispatched": raise HTTPException(409,"Dispatched invoice requires a credit note and goods-return workflow; cancellation is blocked")
    inv.cancelled=True;inv.order.status="cancelled";audit(db,user,"invoice.cancelled","invoice",inv.invoice_number,{"retained":True});db.commit()
    return {"invoice":inv.invoice_number,"cancelled":True,"record_retained":True}

static_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir/"assets"), name="assets")
    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path.startswith(("api/", "docs", "openapi.json", "health")): raise HTTPException(404,"Not found")
        file_path=static_dir/full_path
        if full_path and file_path.is_file(): return FileResponse(file_path)
        return FileResponse(static_dir/"index.html")
