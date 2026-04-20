"""Zach's Liquor Store — Main FastAPI Application v2"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import create_tables, AsyncSessionLocal
from app.routers.auth import router as auth_router
from app.routers.analytics import router as analytics_router
from app.routers.products_expenses import products_router, expenses_router, deals_router
from app.routers.sales import router as sales_router
from app.routers.suppliers import router as suppliers_router
from app.core.config import get_settings

settings = get_settings()
scheduler = AsyncIOScheduler()

async def scheduled_deal_check():
    try:
        async with AsyncSessionLocal() as db:
            from app.services.supplier_monitor import run_deal_check
            count = await run_deal_check(db)
            if count > 0: print(f"[Scheduler] {count} new deals")
    except Exception as e:
        print(f"[Scheduler] Error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    scheduler.add_job(scheduled_deal_check,"interval",
        minutes=settings.supplier_check_interval_minutes,id="deal_check")
    scheduler.start()
    print(f"✓ Zach's Liquor Store API v2 ({settings.environment})")
    yield
    scheduler.shutdown()

app = FastAPI(title="Zach's Liquor Store API",version="2.0.0",lifespan=lifespan,
    docs_url="/docs" if settings.environment!="production" else None)

app.add_middleware(CORSMiddleware,
    allow_origins=[settings.frontend_url,"http://localhost:5173","http://localhost:3000"],
    allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(products_router)
app.include_router(expenses_router)
app.include_router(deals_router)
app.include_router(sales_router)
app.include_router(suppliers_router)

# Promotions
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Promotion, User
from app.core.security import get_current_user
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

promo_router = APIRouter(prefix="/promotions", tags=["promotions"])

class PromoCreate(BaseModel):
    title: str; description: Optional[str]=None; promo_type: str="Percentage Off"
    discount_value: Optional[float]=None; buy_qty: Optional[int]=None; get_qty: Optional[int]=None
    category: Optional[str]=None; product_name: Optional[str]=None
    start_date: Optional[str]=None; end_date: Optional[str]=None
    is_active: bool=True; notes: Optional[str]=None

@promo_router.get("/")
async def list_promos(db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Promotion).order_by(Promotion.created_at.desc()))
    def fmt(p):
        return {"id":p.id,"title":p.title,"description":p.description,"promo_type":p.promo_type,
                "discount_value":p.discount_value,"buy_qty":p.buy_qty,"get_qty":p.get_qty,
                "category":p.category,"product_name":p.product_name,
                "start_date":p.start_date.isoformat() if p.start_date else None,
                "end_date":p.end_date.isoformat() if p.end_date else None,
                "is_active":p.is_active,"notes":p.notes}
    return [fmt(p) for p in r.scalars()]

@promo_router.post("/")
async def create_promo(data: PromoCreate,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    p=Promotion(title=data.title,description=data.description,promo_type=data.promo_type,
        discount_value=data.discount_value,buy_qty=data.buy_qty,get_qty=data.get_qty,
        category=data.category,product_name=data.product_name,
        start_date=datetime.fromisoformat(data.start_date) if data.start_date else None,
        end_date=datetime.fromisoformat(data.end_date) if data.end_date else None,
        is_active=data.is_active,notes=data.notes)
    db.add(p); await db.commit(); await db.refresh(p)
    return {"id":p.id,"title":p.title}

@promo_router.patch("/{promo_id}")
async def update_promo(promo_id: int,data: dict,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Promotion).where(Promotion.id==promo_id))
    p=r.scalar_one_or_none()
    if not p: return {"error":"not found"}
    for k,v in data.items(): setattr(p,k,v)
    await db.commit(); return {"ok":True}

@promo_router.delete("/{promo_id}")
async def delete_promo(promo_id: int,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r=await db.execute(select(Promotion).where(Promotion.id==promo_id))
    p=r.scalar_one_or_none()
    if p: await db.delete(p); await db.commit()
    return {"ok":True}

app.include_router(promo_router)

@app.get("/")
async def root(): return {"app":"Zach's Liquor Store","version":"2.0.0","status":"running"}

@app.get("/health")
async def health(): return {"status":"healthy","environment":settings.environment}
