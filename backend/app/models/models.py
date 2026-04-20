"""
Zach's Liquor Store — Database Models (v2)
Upgraded with store-specific product taxonomy, demand tracking, and historical sales.
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
    Text, Boolean, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class MFAType(str, enum.Enum):
    totp = "totp"
    sms  = "sms"
    none = "none"


# ── Users ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50), unique=True, index=True, nullable=False)
    email           = Column(String(100), unique=True, index=True, nullable=False)
    full_name       = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    phone           = Column(String(20))
    is_active       = Column(Boolean, default=True)
    is_admin        = Column(Boolean, default=False)
    mfa_enabled     = Column(Boolean, default=False)
    mfa_type        = Column(String(10), default="none")
    totp_secret     = Column(String(100))
    totp_verified   = Column(Boolean, default=False)
    backup_codes    = Column(JSON)
    last_login      = Column(DateTime(timezone=True))
    failed_attempts = Column(Integer, default=0)
    locked_until    = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    sales           = relationship("Sale", back_populates="user")
    expenses        = relationship("Expense", back_populates="user")


# ── Supplier ──────────────────────────────────────────────────────────────────
class Supplier(Base):
    __tablename__ = "suppliers"
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(150), unique=True, nullable=False)
    contact_email   = Column(String(100))
    phone           = Column(String(30))
    address         = Column(Text)
    website         = Column(String(255))
    portal_url      = Column(String(255))
    portal_username = Column(String(100))
    portal_password = Column(String(255))
    portal_type     = Column(String(30))
    lead_days       = Column(Integer, default=5)
    notes           = Column(Text)
    is_active       = Column(Boolean, default=True)
    monitor_deals   = Column(Boolean, default=False)
    last_checked    = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    products        = relationship("Product", back_populates="supplier_rel")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier_rel")
    deals           = relationship("SupplierDeal", back_populates="supplier_rel")


# ── Products (upgraded schema) ────────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"
    id               = Column(Integer, primary_key=True, index=True)
    # Identity
    name             = Column(String(200), nullable=False, index=True)
    display_name     = Column(String(200))
    raw_name         = Column(String(200))       # POS original name
    sku              = Column(String(50), unique=True, index=True)
    barcode          = Column(String(50), unique=True, nullable=True)
    brand_family     = Column(String(100), index=True)
    # Taxonomy
    category         = Column(String(100), index=True)   # Beer, Hard Liquor, Wine, Tobacco, Vapes, Cool Drinks, Snacks
    subcategory      = Column(String(100))               # Tequila, Vodka, Whiskey, Cognac, etc.
    product_line     = Column(String(100))               # Core, Blanco, Reposado, etc.
    # Size normalization
    size_label       = Column(String(30))                # "50ml", "750ml", "12-pack"
    size_bucket      = Column(String(50))                # Mini Shot, Fifth, Half Gallon, 12-Pack
    nominal_ml       = Column(Integer)                   # 50, 375, 750, 1750
    pack_type        = Column(String(30))                # Bottle, Can, Pack, Carton
    unit             = Column(String(30), default="each")
    # Pricing
    cost_price       = Column(Float, nullable=False, default=0.0)
    sell_price       = Column(Float, nullable=False, default=0.0)
    predicted_price  = Column(Float)
    min_price        = Column(Float)
    price_tier       = Column(String(20))                # Budget, Value, Mid-range, Premium, Luxury
    # Demand & Inventory intelligence
    demand_type      = Column(String(30))                # Impulse, Core, Bulk, Daily, Seasonal
    demand_band      = Column(String(10))                # Low, Medium, High
    quantity_sold_proxy = Column(Integer, default=1)     # from POS Best Items
    reorder_priority = Column(String(10), default="Low") # Low, Medium, High
    # Stock
    stock            = Column(Integer, default=0)
    reorder_point    = Column(Integer, default=5)
    reorder_qty      = Column(Integer, default=12)
    # Relations
    supplier_id      = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier_name    = Column(String(150))               # denormalized for speed
    # Flags
    is_active        = Column(Boolean, default=True)
    is_seasonal      = Column(Boolean, default=False)
    exclude_flag     = Column(Boolean, default=False)
    season_tags      = Column(JSON)
    # Meta
    description      = Column(Text)
    notes            = Column(Text)
    image_url        = Column(String(500))
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    supplier_rel = relationship("Supplier", back_populates="products")
    sale_items   = relationship("SaleItem", back_populates="product")
    adjustments  = relationship("StockAdjustment", back_populates="product")
    po_items     = relationship("PurchaseOrderItem", back_populates="product")


# ── Sales ─────────────────────────────────────────────────────────────────────
class Sale(Base):
    __tablename__ = "sales"
    id             = Column(Integer, primary_key=True, index=True)
    sale_date      = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    total_revenue  = Column(Float, default=0.0)
    total_cost     = Column(Float, default=0.0)
    total_profit   = Column(Float, default=0.0)
    payment_method = Column(String(20), default="cash")
    is_historical  = Column(Boolean, default=False)  # True = imported, don't adjust stock
    notes          = Column(Text)
    created_by     = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    user           = relationship("User", back_populates="sales")
    items          = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"
    id         = Column(Integer, primary_key=True, index=True)
    sale_id    = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity   = Column(Integer, nullable=False)
    unit_cost  = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal   = Column(Float, nullable=False)
    profit     = Column(Float, nullable=False)
    sale       = relationship("Sale", back_populates="items")
    product    = relationship("Product", back_populates="sale_items")


# ── Historical Sales Summary ──────────────────────────────────────────────────
class HistoricalSalesSummary(Base):
    """Monthly/yearly revenue totals imported from POS reports."""
    __tablename__ = "historical_sales_summary"
    id           = Column(Integer, primary_key=True, index=True)
    period_type  = Column(String(10))   # "year", "month", "week"
    year         = Column(Integer, index=True)
    month        = Column(Integer, nullable=True)
    week         = Column(Integer, nullable=True)
    revenue      = Column(Float, default=0.0)
    transactions = Column(Integer, default=0)
    source       = Column(String(50), default="pos_import")
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


# ── Expenses ──────────────────────────────────────────────────────────────────
class ExpenseCategory(Base):
    __tablename__ = "expense_categories"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    color       = Column(String(7), default="#888780")
    expenses    = relationship("Expense", back_populates="category_rel")


class Expense(Base):
    __tablename__ = "expenses"
    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(200), nullable=False)
    amount       = Column(Float, nullable=False)
    category_id  = Column(Integer, ForeignKey("expense_categories.id"), nullable=True)
    expense_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    vendor       = Column(String(150))
    receipt_url  = Column(String(500))
    notes        = Column(Text)
    is_recurring = Column(Boolean, default=False)
    recurrence   = Column(String(20))
    created_by   = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    category_rel = relationship("ExpenseCategory", back_populates="expenses")
    user         = relationship("User", back_populates="expenses")


# ── Promotions ────────────────────────────────────────────────────────────────
class Promotion(Base):
    __tablename__ = "promotions"
    id            = Column(Integer, primary_key=True, index=True)
    title         = Column(String(200), nullable=False)
    description   = Column(Text)
    promo_type    = Column(String(30))   # Percentage Off, Dollar Off, Buy X Get Y, etc.
    discount_value= Column(Float)
    buy_qty       = Column(Integer)
    get_qty       = Column(Integer)
    category      = Column(String(100))
    product_name  = Column(String(200))
    start_date    = Column(DateTime(timezone=True))
    end_date      = Column(DateTime(timezone=True))
    is_active     = Column(Boolean, default=True)
    notes         = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())


# ── Stock Adjustments ─────────────────────────────────────────────────────────
class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"
    id              = Column(Integer, primary_key=True, index=True)
    product_id      = Column(Integer, ForeignKey("products.id"), nullable=False)
    adjustment_type = Column(String(30))
    quantity_change = Column(Integer, nullable=False)
    quantity_before = Column(Integer)
    quantity_after  = Column(Integer)
    reason          = Column(Text)
    adjusted_by     = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    product         = relationship("Product", back_populates="adjustments")


# ── Purchase Orders ───────────────────────────────────────────────────────────
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id            = Column(Integer, primary_key=True, index=True)
    supplier_id   = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    status        = Column(String(30), default="pending")
    order_date    = Column(DateTime(timezone=True), server_default=func.now())
    expected_date = Column(DateTime(timezone=True))
    received_date = Column(DateTime(timezone=True))
    total_cost    = Column(Float, default=0.0)
    notes         = Column(Text)
    created_by    = Column(Integer, ForeignKey("users.id"), nullable=True)
    supplier_rel  = relationship("Supplier", back_populates="purchase_orders")
    items         = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id                = Column(Integer, primary_key=True, index=True)
    order_id          = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id        = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_ordered  = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_cost         = Column(Float, nullable=False)
    subtotal          = Column(Float, nullable=False)
    order             = relationship("PurchaseOrder", back_populates="items")
    product           = relationship("Product", back_populates="po_items")


# ── Supplier Deals ────────────────────────────────────────────────────────────
class SupplierDeal(Base):
    __tablename__ = "supplier_deals"
    id            = Column(Integer, primary_key=True, index=True)
    supplier_id   = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    title         = Column(String(300), nullable=False)
    description   = Column(Text)
    discount_pct  = Column(Float)
    original_price= Column(Float)
    deal_price    = Column(Float)
    product_name  = Column(String(200))
    category      = Column(String(100))
    valid_from    = Column(DateTime(timezone=True))
    valid_until   = Column(DateTime(timezone=True))
    deal_url      = Column(String(500))
    is_read       = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)
    source        = Column(String(50))
    raw_data      = Column(JSON)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    supplier_rel  = relationship("Supplier", back_populates="deals")


# ── Audit Log ─────────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    action      = Column(String(100), nullable=False)
    resource    = Column(String(100))
    resource_id = Column(Integer)
    details     = Column(JSON)
    ip_address  = Column(String(45))
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
