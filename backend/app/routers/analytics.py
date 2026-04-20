"""
Zach's Liquor Store — Analytics Router v2
Store-specific: category breakdown, hourly heatmap, brand performance, P&L
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, text
from typing import Optional
from datetime import datetime, timedelta, date
from app.database import get_db
from app.models.models import Sale, SaleItem, Product, Expense, User, HistoricalSalesSummary
from app.core.security import get_current_user
try:
    from app.services.seasonal import SEASONS, get_season_windows, compute_yoy_comparison
except ImportError:
    SEASONS = {}
    def get_season_windows(k, y): return []
    async def compute_yoy_comparison(db, w, k): return {}

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    r = await db.execute(select(func.coalesce(func.sum(Sale.total_revenue),0),
        func.coalesce(func.sum(Sale.total_profit),0),func.count(Sale.id)))
    total_rev, total_profit, total_sales = r.one()

    r = await db.execute(select(func.coalesce(func.sum(Sale.total_revenue),0),
        func.coalesce(func.sum(Sale.total_profit),0))
        .where(Sale.sale_date >= month_start))
    month_rev, month_profit = r.one()

    r = await db.execute(select(func.coalesce(func.sum(Sale.total_revenue),0))
        .where(Sale.sale_date >= today_start))
    today_rev = r.scalar()

    r = await db.execute(select(func.count(Product.id),
        func.coalesce(func.sum(Product.stock*Product.cost_price),0),
        func.coalesce(func.sum(Product.stock*Product.sell_price),0))
        .where(Product.is_active==True))
    total_products, inv_cost, inv_retail = r.one()

    r = await db.execute(select(func.count(Product.id)).where(
        Product.is_active==True, Product.stock<=Product.reorder_point, Product.stock>0))
    low_stock = r.scalar()

    r = await db.execute(select(func.count(Product.id)).where(
        Product.is_active==True, Product.stock==0))
    out_of_stock = r.scalar()

    r = await db.execute(select(func.coalesce(func.sum(Expense.amount),0))
        .where(Expense.expense_date >= month_start))
    month_expenses = r.scalar()

    # Category breakdown this month
    r = await db.execute(select(Product.category,
        func.coalesce(func.sum(SaleItem.subtotal),0).label("revenue"),
        func.coalesce(func.sum(SaleItem.quantity),0).label("units"))
        .join(SaleItem, SaleItem.product_id==Product.id)
        .join(Sale, Sale.id==SaleItem.sale_id)
        .where(Sale.sale_date >= month_start)
        .group_by(Product.category).order_by(text("revenue desc")))
    cat_breakdown = [{"category":row[0],"revenue":round(row[1],2),"units":row[2]} for row in r]

    # Historical context
    r = await db.execute(select(HistoricalSalesSummary.year,
        func.sum(HistoricalSalesSummary.revenue).label("rev"))
        .where(HistoricalSalesSummary.period_type=="year")
        .group_by(HistoricalSalesSummary.year).order_by(HistoricalSalesSummary.year))
    yearly_hist = [{"year":row[0],"revenue":round(row[1],2)} for row in r]

    margin = round((total_profit/total_rev*100),1) if total_rev else 0
    return {
        "total_revenue": round(total_rev,2),
        "total_profit": round(total_profit,2),
        "profit_margin_pct": margin,
        "total_sales_count": total_sales,
        "today_revenue": round(today_rev,2),
        "month_revenue": round(month_rev,2),
        "month_profit": round(month_profit,2),
        "month_expenses": round(month_expenses,2),
        "month_net": round(month_profit-month_expenses,2),
        "inventory_cost_value": round(inv_cost,2),
        "inventory_retail_value": round(inv_retail,2),
        "total_products": total_products,
        "low_stock_count": low_stock,
        "out_of_stock_count": out_of_stock,
        "category_breakdown": cat_breakdown,
        "yearly_historical": yearly_hist,
    }


@router.get("/daily")
async def daily(days: int=Query(30,le=365),db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    since = datetime.utcnow() - timedelta(days=days)
    r = await db.execute(select(
        func.date(Sale.sale_date).label("d"),
        func.coalesce(func.sum(Sale.total_revenue),0),
        func.coalesce(func.sum(Sale.total_profit),0),
        func.count(Sale.id))
        .where(Sale.sale_date>=since)
        .group_by(func.date(Sale.sale_date))
        .order_by(func.date(Sale.sale_date)))
    return [{"date":str(row[0]),"revenue":round(row[1],2),"profit":round(row[2],2),"transactions":row[3]} for row in r]


@router.get("/monthly")
async def monthly(year: Optional[int]=None,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    yr = year or datetime.utcnow().year
    r = await db.execute(select(
        extract("month",Sale.sale_date).label("m"),
        func.coalesce(func.sum(Sale.total_revenue),0),
        func.coalesce(func.sum(Sale.total_profit),0),
        func.count(Sale.id))
        .where(extract("year",Sale.sale_date)==yr)
        .group_by(extract("month",Sale.sale_date))
        .order_by(extract("month",Sale.sale_date)))
    months=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return [{"month":months[int(row[0])],"month_num":int(row[0]),"revenue":round(row[1],2),
             "profit":round(row[2],2),"transactions":row[3]} for row in r]


@router.get("/yearly")
async def yearly(db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r = await db.execute(select(
        extract("year",Sale.sale_date).label("y"),
        func.coalesce(func.sum(Sale.total_revenue),0),
        func.coalesce(func.sum(Sale.total_profit),0),
        func.count(Sale.id))
        .group_by(extract("year",Sale.sale_date))
        .order_by(extract("year",Sale.sale_date)))
    return [{"year":int(row[0]),"revenue":round(row[1],2),"profit":round(row[2],2),"transactions":row[3]} for row in r]


@router.get("/category-breakdown")
async def category_breakdown(period_days: int=Query(30),db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    since = datetime.utcnow()-timedelta(days=period_days)
    r = await db.execute(select(
        Product.category,Product.subcategory,
        func.coalesce(func.sum(SaleItem.subtotal),0).label("revenue"),
        func.coalesce(func.sum(SaleItem.profit),0).label("profit"),
        func.coalesce(func.sum(SaleItem.quantity),0).label("units"))
        .join(SaleItem,SaleItem.product_id==Product.id)
        .join(Sale,Sale.id==SaleItem.sale_id)
        .where(Sale.sale_date>=since)
        .group_by(Product.category,Product.subcategory)
        .order_by(text("revenue desc")))
    return [{"category":row[0],"subcategory":row[1],"revenue":round(row[2],2),
             "profit":round(row[3],2),"units":row[4]} for row in r]


@router.get("/hourly-heatmap")
async def hourly_heatmap(period_days: int=Query(30),db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    since = datetime.utcnow()-timedelta(days=period_days)
    r = await db.execute(select(
        extract("hour",Sale.sale_date).label("h"),
        extract("dow",Sale.sale_date).label("dow"),
        func.coalesce(func.sum(Sale.total_revenue),0).label("rev"))
        .where(Sale.sale_date>=since)
        .group_by(extract("hour",Sale.sale_date),extract("dow",Sale.sale_date))
        .order_by(extract("hour",Sale.sale_date)))
    return [{"hour":int(row[0]),"day_of_week":int(row[1]),"revenue":round(row[2],2)} for row in r]


@router.get("/top-products")
async def top_products(limit: int=Query(20),period_days: int=Query(30),
    category: Optional[str]=None,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    since = datetime.utcnow()-timedelta(days=period_days)
    q = select(Product.id,Product.name,Product.brand_family,Product.category,
        Product.subcategory,Product.size_bucket,Product.price_tier,
        Product.sell_price,Product.cost_price,
        func.coalesce(func.sum(SaleItem.subtotal),0).label("revenue"),
        func.coalesce(func.sum(SaleItem.profit),0).label("profit"),
        func.coalesce(func.sum(SaleItem.quantity),0).label("units"))\
        .join(SaleItem,SaleItem.product_id==Product.id)\
        .join(Sale,Sale.id==SaleItem.sale_id)\
        .where(Sale.sale_date>=since)
    if category:
        q = q.where(Product.category==category)
    q = q.group_by(Product.id,Product.name,Product.brand_family,Product.category,
        Product.subcategory,Product.size_bucket,Product.price_tier,
        Product.sell_price,Product.cost_price)\
        .order_by(text("revenue desc")).limit(limit)
    r = await db.execute(q)
    return [{"id":row[0],"name":row[1],"brand_family":row[2],"category":row[3],
             "subcategory":row[4],"size_bucket":row[5],"price_tier":row[6],
             "sell_price":row[7],"cost_price":row[8],
             "revenue":round(row[9],2),"profit":round(row[10],2),"units":row[11]} for row in r]


@router.get("/bottom-products")
async def bottom_products(limit: int=Query(10),period_days: int=Query(30),
    db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    since = datetime.utcnow()-timedelta(days=period_days)
    r = await db.execute(select(Product.id,Product.name,Product.category,
        Product.size_bucket,Product.stock,
        func.coalesce(func.sum(SaleItem.subtotal),0).label("revenue"),
        func.coalesce(func.sum(SaleItem.quantity),0).label("units"))
        .join(SaleItem,SaleItem.product_id==Product.id,isouter=True)
        .join(Sale,Sale.id==SaleItem.sale_id,isouter=True)
        .where(Product.is_active==True)
        .group_by(Product.id,Product.name,Product.category,Product.size_bucket,Product.stock)
        .order_by(text("revenue asc")).limit(limit))
    return [{"id":row[0],"name":row[1],"category":row[2],"size_bucket":row[3],
             "stock":row[4],"revenue":round(row[5],2),"units":row[6]} for row in r]


@router.get("/pl-summary")
async def pl_summary(year: Optional[int]=None,db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    yr = year or datetime.utcnow().year
    r = await db.execute(select(
        extract("month",Sale.sale_date).label("m"),
        func.coalesce(func.sum(Sale.total_revenue),0),
        func.coalesce(func.sum(Sale.total_cost),0),
        func.coalesce(func.sum(Sale.total_profit),0))
        .where(extract("year",Sale.sale_date)==yr)
        .group_by(extract("month",Sale.sale_date))
        .order_by(extract("month",Sale.sale_date)))
    sales_rows = {int(row[0]):{"revenue":row[1],"cogs":row[2],"gross_profit":row[3]} for row in r}

    r = await db.execute(select(
        extract("month",Expense.expense_date).label("m"),
        func.coalesce(func.sum(Expense.amount),0))
        .where(extract("year",Expense.expense_date)==yr)
        .group_by(extract("month",Expense.expense_date)))
    exp_rows = {int(row[0]):row[1] for row in r}

    months=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    result=[]
    for m in range(1,13):
        s=sales_rows.get(m,{"revenue":0,"cogs":0,"gross_profit":0})
        exp=exp_rows.get(m,0)
        result.append({"month":months[m],"month_num":m,
            "revenue":round(s["revenue"],2),"cogs":round(s["cogs"],2),
            "gross_profit":round(s["gross_profit"],2),
            "expenses":round(exp,2),"net_profit":round(s["gross_profit"]-exp,2)})
    return result


@router.get("/historical-summary")
async def historical_summary(db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    r = await db.execute(select(HistoricalSalesSummary)
        .order_by(HistoricalSalesSummary.year,HistoricalSalesSummary.month))
    return [{"period_type":row.period_type,"year":row.year,"month":row.month,
             "revenue":round(row.revenue,2),"transactions":row.transactions} for row in r.scalars()]


@router.get("/seasonal")
async def seasonal(season_key: str="christmas",year: Optional[int]=None,
    db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    yr=year or datetime.utcnow().year
    windows=get_season_windows(season_key,yr)
    if not windows: return {"error":"unknown season"}
    return await compute_yoy_comparison(db,windows,season_key)


@router.get("/brand-performance")
async def brand_performance(period_days: int=Query(30),db: AsyncSession=Depends(get_db),_: User=Depends(get_current_user)):
    since=datetime.utcnow()-timedelta(days=period_days)
    r=await db.execute(select(Product.brand_family,Product.category,
        func.coalesce(func.sum(SaleItem.subtotal),0).label("revenue"),
        func.coalesce(func.sum(SaleItem.quantity),0).label("units"))
        .join(SaleItem,SaleItem.product_id==Product.id)
        .join(Sale,Sale.id==SaleItem.sale_id)
        .where(Sale.sale_date>=since,Product.brand_family!="",Product.brand_family!=None)
        .group_by(Product.brand_family,Product.category)
        .order_by(text("revenue desc")).limit(20))
    return [{"brand":row[0],"category":row[1],"revenue":round(row[2],2),"units":row[3]} for row in r]


@router.get("/seasons-overview")
async def seasons_overview(year: int=2026, db: AsyncSession=Depends(get_db), _: User=Depends(get_current_user)):
    """All seasons data for a given year — for the seasonal page overview."""
    from app.models.models import Sale, SaleItem, Product
    results = []
    for key, s in SEASONS.items():
        try:
            start = datetime(year, s["month"], s["day_start"])
            end   = datetime(year, s["month"], s["day_end"], 23, 59, 59)
            # Also get prior year
            start_py = datetime(year-1, s["month"], s["day_start"])
            end_py   = datetime(year-1, s["month"], s["day_end"], 23, 59, 59)
        except ValueError:
            continue
        r = await db.execute(select(
            func.coalesce(func.sum(Sale.total_revenue),0),
            func.coalesce(func.sum(Sale.total_profit),0),
            func.count(Sale.id))
            .where(Sale.sale_date>=start, Sale.sale_date<=end))
        rev, profit, txns = r.one()
        r2 = await db.execute(select(
            func.coalesce(func.sum(Sale.total_revenue),0))
            .where(Sale.sale_date>=start_py, Sale.sale_date<=end_py))
        prev_rev = r2.scalar()
        pct = round((rev-prev_rev)/prev_rev*100,1) if prev_rev else None
        results.append({
            "key": key, "label": s["label"],
            "month": s["month"], "day_start": s["day_start"], "day_end": s["day_end"],
            "revenue": round(rev,2), "profit": round(profit,2), "transactions": txns,
            "prior_revenue": round(prev_rev,2), "yoy_pct": pct,
        })
    return sorted(results, key=lambda x: (x["month"], x["day_start"]))
