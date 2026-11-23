from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Integer, Boolean, Date, DateTime, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, index=True)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[Role] = relationship()

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    state: Mapped[str] = mapped_column(String(80), default="Tamil Nadu")
    gstin: Mapped[str] = mapped_column(String(15), default="")
    phone: Mapped[str] = mapped_column(String(30), default="")
    address: Mapped[str] = mapped_column(String(300), default="")

class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    state: Mapped[str] = mapped_column(String(80), default="Tamil Nadu")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    category: Mapped[str] = mapped_column(String(40), default="Snacks")
    pack_size_g: Mapped[int] = mapped_column(Integer, default=200)
    hsn: Mapped[str] = mapped_column(String(12), default="210690")
    selling_price_paise: Mapped[int] = mapped_column(Integer, default=5000)
    gst_rate_bps: Mapped[int] = mapped_column(Integer, default=500)
    finished_stock: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0"))

class Material(Base):
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    kind: Mapped[str] = mapped_column(String(24), index=True)  # raw | packaging
    unit: Mapped[str] = mapped_column(String(24))
    stock: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0"))
    # Weighted average can be fractional paisa (benchmark flour rate: 4,312.5 paisa/kg).
    avg_cost_paise: Mapped[Decimal] = mapped_column(Numeric(16, 3), default=Decimal("0"))
    last_cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    quarantined: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0"))

class BOMItem(Base):
    __tablename__ = "bom_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    per_output: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("200"))
    product: Mapped[Product] = relationship()
    material: Mapped[Material] = relationship()

class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    purchased_at: Mapped[date] = mapped_column(Date, default=date.today)
    total_paise: Mapped[int] = mapped_column(Integer, default=0)
    supplier: Mapped[Supplier | None] = relationship()

class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id"), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    unit_cost_paise: Mapped[int] = mapped_column(Integer)

class ProductionRun(Base):
    __tablename__ = "production_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    batch_size: Mapped[int] = mapped_column(Integer)
    expected_output: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    actual_output: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    damaged_pouches: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0"))
    wastage_percent: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=Decimal("0"))
    labour_paise: Mapped[int] = mapped_column(Integer, default=0)
    utilities_paise: Mapped[int] = mapped_column(Integer, default=0)
    material_cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    cost_per_packet_paise: Mapped[int] = mapped_column(Integer, default=0)
    production_date: Mapped[date] = mapped_column(Date, default=date.today)
    variance_data: Mapped[str] = mapped_column(Text, default="{}")

class StockMovement(Base):
    __tablename__ = "stock_movements"
    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id"), nullable=True, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)
    movement_type: Mapped[str] = mapped_column(String(24), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    source_document: Mapped[str] = mapped_column(String(80), index=True)
    note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    material: Mapped[Material | None] = relationship()
    product: Mapped[Product | None] = relationship()

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    salesman_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_paise: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    customer: Mapped[Customer] = relationship()
    product: Mapped[Product] = relationship()

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    invoice_date: Mapped[date] = mapped_column(Date, default=date.today)
    taxable_paise: Mapped[int] = mapped_column(Integer)
    cgst_paise: Mapped[int] = mapped_column(Integer, default=0)
    sgst_paise: Mapped[int] = mapped_column(Integer, default=0)
    igst_paise: Mapped[int] = mapped_column(Integer, default=0)
    total_paise: Mapped[int] = mapped_column(Integer)
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[Order] = relationship()

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    amount_paise: Mapped[int] = mapped_column(Integer)
    paid_at: Mapped[date] = mapped_column(Date, default=date.today)
    reference: Mapped[str] = mapped_column(String(80), default="")
    invoice: Mapped[Invoice] = relationship()

class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(80))
    amount_paise: Mapped[int] = mapped_column(Integer)
    spent_at: Mapped[date] = mapped_column(Date, default=date.today)
    reference: Mapped[str] = mapped_column(String(80), default="")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

Index("ix_stock_created_material", StockMovement.created_at, StockMovement.material_id)
