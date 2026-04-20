"""
Suppliers router — full CRUD including portal credential management
for deal monitoring (Breakthru, RNDC, custom).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.models import Supplier, User
from app.core.security import get_current_user

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


class SupplierIn(BaseModel):
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    portal_url: Optional[str] = None
    portal_username: Optional[str] = None
    portal_password: Optional[str] = None
    portal_type: Optional[str] = "custom"
    lead_days: int = 5
    notes: Optional[str] = None
    monitor_deals: bool = False


def sup_out(s: Supplier) -> dict:
    return {
        "id": s.id, "name": s.name,
        "contact_email": s.contact_email, "phone": s.phone,
        "address": s.address, "website": s.website,
        "portal_url": s.portal_url,
        "portal_username": s.portal_username,
        # Never return password — mask it
        "portal_password_set": bool(s.portal_password),
        "portal_type": s.portal_type,
        "lead_days": s.lead_days, "notes": s.notes,
        "is_active": s.is_active, "monitor_deals": s.monitor_deals,
        "last_checked": s.last_checked, "created_at": s.created_at,
    }


@router.get("/")
async def list_suppliers(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    r = await db.execute(select(Supplier).where(Supplier.is_active == True).order_by(Supplier.name))
    return [sup_out(s) for s in r.scalars().all()]


@router.post("/", status_code=201)
async def create_supplier(payload: SupplierIn, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    r = await db.execute(select(Supplier).where(Supplier.name == payload.name))
    if r.scalar_one_or_none():
        raise HTTPException(400, "Supplier name already exists")
    s = Supplier(**payload.model_dump())
    db.add(s); await db.commit(); await db.refresh(s)
    return sup_out(s)


@router.get("/{supplier_id}")
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    r = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    s = r.scalar_one_or_none()
    if not s: raise HTTPException(404, "Supplier not found")
    return sup_out(s)


@router.patch("/{supplier_id}")
async def update_supplier(supplier_id: int, payload: SupplierIn, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    r = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    s = r.scalar_one_or_none()
    if not s: raise HTTPException(404, "Supplier not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        # Don't overwrite password with empty string
        if k == "portal_password" and not v:
            continue
        setattr(s, k, v)
    await db.commit(); await db.refresh(s)
    return sup_out(s)


@router.delete("/{supplier_id}", status_code=204)
async def delete_supplier(supplier_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    r = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    s = r.scalar_one_or_none()
    if not s: raise HTTPException(404, "Supplier not found")
    s.is_active = False
    await db.commit()
