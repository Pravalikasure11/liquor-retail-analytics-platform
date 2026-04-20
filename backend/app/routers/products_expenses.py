"""Zach's Liquor Store — Products, Expenses, Deals routers (v2)"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, text
from typing import Optional
from app.database import get_db
from app.models.models import Product, Expense, ExpenseCategory, SupplierDeal, User
from app.core.security import get_current_user
from pydantic import BaseModel
from typing import List

products_router = APIRouter(prefix="/products", tags=["products"])
expenses_router = APIRouter(prefix="/expenses", tags=["expenses"])
deals_router    = APIRouter(prefix="/deals",    tags=["deals"])


# ── Product Schemas ───────────────────────────────────────────────────────────
class ProductCreate(BaseModel):
    name: str
    display_name: Optional[str]=None
    raw_name: Optional[str]=None
    sku: Optional[str]=None
    brand_family: Optional[str]=None
    category: str
    subcategory: Optional[str]=None
    product_line: Optional[str]=None
    size_label: Optional[str]=None
    size_bucket: Optional[str]=None
    nominal_ml: Optional[int]=None
    pack_type: Optional[str]=None
    price_tier: Optional[str]="Value"
    demand_type: Optional[str]=None
    demand_band: Optional[str]="Low"
    reorder_priority: Optional[str]="Low"
    unit: Optional[str]="each"
    cost_price: float=0.0
    sell_price: float=0.0
    stock: int=0
    reorder_point: int=5
    reorder_qty: int=12
    description: Optional[str]=None
    supplier_name: Optional[str]=None
    is_active: bool=True
    is_seasonal: bool=False
    season_tags: Optional[list]=None

class ProductUpdate(BaseModel):
    name: Optional[str]=None
    display_name: Optional[str]=None
    brand_family: Optional[str]=None
    category: Optional[str]=None
    subcategory: Optional[str]=None
    product_line: Optional[str]=None
    size_label: Optional[str]=None
    size_bucket: Optional[str]=None
    nominal_ml: Optional[int]=None
    price_tier: Optional[str]=None
    demand_type: Optional[str]=None
    demand_band: Optional[str]=None
    cost_price: Optional[float]=None
    sell_price: Optional[float]=None
    stock: Optional[int]=None
    reorder_point: Optional[int]=None
    reorder_qty: Optional[int]=None
    description: Optional[str]=None
    supplier_name: Optional[str]=None
    is_active: Optional[bool]=None
    is_seasonal: Optional[bool]=None
    season_tags: Optional[list]=None


def prod_dict(p: Product) -> dict:
    return {
        "id":p.id,"name":p.name,"display_name":p.display_name,"raw_name":p.raw_name,
        "sku":p.sku,"barcode":p.barcode,"brand_family":p.brand_family,
        "category":p.category,"subcategory":p.subcategory,"product_line":p.product_line,
        "size_label":p.size_label,"size_bucket":p.size_bucket,"nominal_ml":p.nominal_ml,
        "pack_type":p.pack_type,"unit":p.unit,"price_tier":p.price_tier,
        "demand_type":p.demand_type,"demand_band":p.demand_band,
        "quantity_sold_proxy":p.quantity_sold_proxy,"reorder_priority":p.reorder_priority,
        "cost_price":p.cost_price,"sell_price":p.sell_price,"predicted_price":p.predicted_price,
        "margin_pct":round((p.sell_price-p.cost_price)/p.sell_price*100,1) if p.sell_price else 0,
        "stock":p.stock,"reorder_point":p.reorder_point,"reorder_qty":p.reorder_qty,
        "supplier_name":p.supplier_name,"supplier_id":p.supplier_id,
        "description":p.description,"notes":p.notes,
        "is_active":p.is_active,"is_seasonal":p.is_seasonal,"exclude_flag":p.exclude_flag,
        "season_tags":p.season_tags,"image_url":p.image_url,
        "created_at":p.created_at.isoformat() if p.created_at else None,
        "updated_at":p.updated_at.isoformat() if p.updated_at else None,
    }


@products_router.get("/")
async def list_products(
    search: Optional[str]=None, category: Optional[str]=None,
    subcategory: Optional[str]=None, brand_family: Optional[str]=None,
    size_bucket: Optional[str]=None, price_tier: Optional[str]=None,
    low_stock: Optional[bool]=None, is_active: Optional[bool]=True,
    skip: int=0, limit: int=500,
    db: AsyncSession=Depends(get_db), _: User=Depends(get_current_user)):
    q = select(Product)
    if is_active is not None: q=q.where(Product.is_active==is_active)
    q=q.where(Product.exclude_flag!=True)
    if search:
        s=f"%{search}%"
        q=q.where(or_(Product.name.ilike(s),Product.brand_family.ilike(s),
                       Product.sku.ilike(s),Product.subcategory.ilike(s)))
    if category:    q=q.where(Product.category==category)
    if subcategory: q=q.where(Product.subcategory==subcategory)
    if brand_family:q=q.where(Product.brand_family.ilike(f"%{brand_family}%"))
    if size_bucket: q=q.where(Product.size_bucket==size_bucket)
    if price_tier:  q=q.where(Product.price_tier==price_tier)
    if low_stock:   q=q.where(Product.stock<=Product.reorder_point)
    q=q.order_by(Product.category,Product.brand_family,Product.name).offset(skip).limit(limit)
    r=await db.execute(q)
    return [prod_dict(p) for p in r.scalars()]


@products_router.get("/categories")
async def get_categories(db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Product.category,func.count(Product.id))
        .where(Product.is_active==True,Product.exclude_flag!=True)
        .group_by(Product.category).order_by(Product.category))
    return [{"category":row[0],"count":row[1]} for row in r]


@products_router.get("/price-suggestions")
async def price_suggestions(db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Product).where(Product.is_active==True,
        Product.predicted_price!=None,Product.sell_price!=None))
    result=[]
    for p in r.scalars():
        if p.predicted_price and abs(p.predicted_price-p.sell_price)>0.50:
            result.append({"id":p.id,"name":p.name,"current_price":p.sell_price,
                "suggested_price":p.predicted_price,"potential_gain":round(p.predicted_price-p.sell_price,2)})
    return sorted(result,key=lambda x:-abs(x["potential_gain"]))


@products_router.get("/{product_id}")
async def get_product(product_id: int,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Product).where(Product.id==product_id))
    p=r.scalar_one_or_none()
    if not p: raise HTTPException(404,"Product not found")
    return prod_dict(p)


@products_router.post("/")
async def create_product(data: ProductCreate,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    if not data.sku:
        data.sku=(data.name or "")[:20].upper().replace(" ","-")+"-NEW"
    p=Product(**data.model_dump())
    if data.sell_price: p.predicted_price=round(data.sell_price*1.05,2)
    db.add(p); await db.commit(); await db.refresh(p)
    return prod_dict(p)


@products_router.patch("/{product_id}")
async def update_product(product_id: int,data: ProductUpdate,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Product).where(Product.id==product_id))
    p=r.scalar_one_or_none()
    if not p: raise HTTPException(404,"Not found")
    for k,v in data.model_dump(exclude_none=True).items(): setattr(p,k,v)
    await db.commit(); await db.refresh(p)
    return prod_dict(p)


@products_router.delete("/{product_id}")
async def delete_product(product_id: int,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Product).where(Product.id==product_id))
    p=r.scalar_one_or_none()
    if not p: raise HTTPException(404,"Not found")
    await db.delete(p); await db.commit()
    return {"ok":True}


# ── Expenses ──────────────────────────────────────────────────────────────────
class ExpenseCreate(BaseModel):
    title: str; amount: float; category_id: Optional[int]=None
    expense_date: Optional[str]=None; vendor: Optional[str]=None
    notes: Optional[str]=None; is_recurring: bool=False; recurrence: Optional[str]=None

class ExpenseUpdate(BaseModel):
    title: Optional[str]=None; amount: Optional[float]=None
    category_id: Optional[int]=None; vendor: Optional[str]=None
    notes: Optional[str]=None

@expenses_router.get("/categories")
async def list_expense_categories(db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(ExpenseCategory))
    return [{"id":c.id,"name":c.name,"color":c.color} for c in r.scalars()]

@expenses_router.post("/categories")
async def create_expense_category(data: dict,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    c=ExpenseCategory(name=data["name"],color=data.get("color","#888780"))
    db.add(c); await db.commit(); await db.refresh(c)
    return {"id":c.id,"name":c.name,"color":c.color}

@expenses_router.get("/")
async def list_expenses(skip: int=0,limit: int=100,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Expense).order_by(Expense.expense_date.desc()).offset(skip).limit(limit))
    return [{"id":e.id,"title":e.title,"amount":e.amount,"category_id":e.category_id,
             "vendor":e.vendor,"notes":e.notes,"expense_date":e.expense_date.isoformat() if e.expense_date else None,
             "is_recurring":e.is_recurring,"recurrence":e.recurrence} for e in r.scalars()]

@expenses_router.post("/")
async def create_expense(data: ExpenseCreate,db: AsyncSession=Depends(get_db),u: User=Depends(get_current_user)):
    from datetime import datetime as dt
    exp_date=dt.fromisoformat(data.expense_date) if data.expense_date else dt.utcnow()
    e=Expense(title=data.title,amount=data.amount,category_id=data.category_id,
              expense_date=exp_date,vendor=data.vendor,notes=data.notes,
              is_recurring=data.is_recurring,recurrence=data.recurrence,created_by=u.id)
    db.add(e); await db.commit(); await db.refresh(e)
    return {"id":e.id,"title":e.title,"amount":e.amount}

@expenses_router.patch("/{expense_id}")
async def update_expense(expense_id: int,data: ExpenseUpdate,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Expense).where(Expense.id==expense_id))
    e=r.scalar_one_or_none()
    if not e: raise HTTPException(404,"Not found")
    for k,v in data.model_dump(exclude_none=True).items(): setattr(e,k,v)
    await db.commit(); return {"ok":True}

@expenses_router.delete("/{expense_id}")
async def delete_expense(expense_id: int,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Expense).where(Expense.id==expense_id))
    e=r.scalar_one_or_none()
    if not e: raise HTTPException(404,"Not found")
    await db.delete(e); await db.commit()
    return {"ok":True}


# ── Deals ─────────────────────────────────────────────────────────────────────
@deals_router.get("/")
async def list_deals(unread_only: bool=False,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    q=select(SupplierDeal).where(SupplierDeal.is_active==True)
    if unread_only: q=q.where(SupplierDeal.is_read==False)
    q=q.order_by(SupplierDeal.created_at.desc()).limit(50)
    r=await db.execute(q)
    return [{"id":d.id,"title":d.title,"description":d.description,"supplier_id":d.supplier_id,
             "discount_pct":d.discount_pct,"product_name":d.product_name,"category":d.category,
             "valid_until":d.valid_until.isoformat() if d.valid_until else None,
             "is_read":d.is_read,"source":d.source,
             "created_at":d.created_at.isoformat() if d.created_at else None} for d in r.scalars()]

@deals_router.get("/unread-count")
async def unread_count(db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(func.count(SupplierDeal.id)).where(
        SupplierDeal.is_active==True,SupplierDeal.is_read==False))
    return {"count":r.scalar()}

@deals_router.post("/{deal_id}/read")
async def mark_read(deal_id: int,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(SupplierDeal).where(SupplierDeal.id==deal_id))
    d=r.scalar_one_or_none()
    if d: d.is_read=True; await db.commit()
    return {"ok":True}

@deals_router.post("/check-now")
async def check_now(supplier_id: Optional[int]=None,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    from app.services.supplier_monitor import run_deal_check
    count=await run_deal_check(db,supplier_id)
    return {"deals_found":count}
