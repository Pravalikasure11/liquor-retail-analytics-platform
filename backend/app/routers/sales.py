"""
Sales router — record sales, list history, delete/reverse.
Auto-deducts stock on sale, restores stock on delete.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, field_validator
from app.database import get_db
from app.models.models import Sale, SaleItem, Product, User
from app.core.security import get_current_user

router = APIRouter(prefix="/sales", tags=["sales"])


class SaleItemIn(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class SaleIn(BaseModel):
    items: List[SaleItemIn]
    notes: Optional[str] = None
    payment_method: str = "cash"
    sale_date: Optional[datetime] = None


def sale_out(s: Sale) -> dict:
    return {
        "id": s.id,
        "sale_date": s.sale_date,
        "total_revenue": s.total_revenue,
        "total_cost": s.total_cost,
        "total_profit": s.total_profit,
        "payment_method": s.payment_method,
        "notes": s.notes,
        "created_at": s.created_at,
        "items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "quantity": i.quantity,
                "unit_cost": i.unit_cost,
                "unit_price": i.unit_price,
                "subtotal": i.subtotal,
                "profit": i.profit,
                "product_name": i.product.name if i.product else None,
                "product_category": i.product.category if i.product else None,
            }
            for i in (s.items or [])
        ],
    }


@router.post("/", status_code=201)
async def record_sale(
    payload: SaleIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_revenue = total_cost = 0.0
    items_data = []

    for item in payload.items:
        r = await db.execute(select(Product).where(Product.id == item.product_id, Product.is_active == True))
        product = r.scalar_one_or_none()
        if not product:
            raise HTTPException(404, f"Product ID {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(400, f"Not enough stock for '{product.name}'. Have: {product.stock}, need: {item.quantity}")

        subtotal = round(item.quantity * product.sell_price, 2)
        cost = round(item.quantity * product.cost_price, 2)
        profit = round(subtotal - cost, 2)
        total_revenue += subtotal
        total_cost += cost
        items_data.append({
            "product": product,
            "quantity": item.quantity,
            "unit_cost": product.cost_price,
            "unit_price": product.sell_price,
            "subtotal": subtotal,
            "profit": profit,
        })

    sale = Sale(
        sale_date=payload.sale_date or datetime.utcnow(),
        total_revenue=round(total_revenue, 2),
        total_cost=round(total_cost, 2),
        total_profit=round(total_revenue - total_cost, 2),
        payment_method=payload.payment_method,
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(sale)
    await db.flush()

    for item_data in items_data:
        product = item_data.pop("product")
        db.add(SaleItem(sale_id=sale.id, product_id=product.id, **item_data))
        product.stock -= item_data["quantity"]

    await db.commit()

    r = await db.execute(
        select(Sale).options(selectinload(Sale.items).selectinload(SaleItem.product))
        .where(Sale.id == sale.id)
    )
    return sale_out(r.scalar_one())


@router.get("/")
async def list_sales(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = (
        select(Sale)
        .options(selectinload(Sale.items).selectinload(SaleItem.product))
        .order_by(Sale.sale_date.desc())
        .offset(skip).limit(limit)
    )
    if start_date:
        q = q.where(Sale.sale_date >= start_date)
    if end_date:
        q = q.where(Sale.sale_date <= end_date)
    r = await db.execute(q)
    return [sale_out(s) for s in r.scalars().all()]


@router.get("/{sale_id}")
async def get_sale(sale_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    r = await db.execute(
        select(Sale).options(selectinload(Sale.items).selectinload(SaleItem.product))
        .where(Sale.id == sale_id)
    )
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Sale not found")
    return sale_out(s)


@router.delete("/{sale_id}", status_code=204)
async def delete_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Reverse a sale — restores stock for all items."""
    r = await db.execute(
        select(Sale).options(selectinload(Sale.items))
        .where(Sale.id == sale_id)
    )
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Sale not found")

    for item in s.items:
        pr = await db.execute(select(Product).where(Product.id == item.product_id))
        product = pr.scalar_one_or_none()
        if product:
            product.stock += item.quantity

    await db.delete(s)
    await db.commit()
