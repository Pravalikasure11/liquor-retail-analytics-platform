"""
Supplier Deal Monitor Service
Polls supplier portals (Breakthru, RNDC, etc.) for deals and promotions.
Runs on a schedule via APScheduler.

NOTE: Requires valid supplier credentials stored in Supplier.portal_username/password.
Credentials are used only to authenticate to the supplier's own portal.
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Portal configurations
PORTAL_CONFIGS = {
    "breakthru": {
        "name": "Breakthru Beverage",
        "login_url": "https://www.breakthrubev.com/login",
        "deals_url": "https://www.breakthrubev.com/promotions",
        "selectors": {
            "deal_items": ".promotion-item, .deal-card",
            "title": ".promotion-title, h3",
            "discount": ".discount-badge, .savings",
            "valid_until": ".expiry-date, .valid-through",
            "price": ".promo-price, .deal-price",
        }
    },
    "rndc": {
        "name": "RNDC (Republic National)",
        "login_url": "https://www.rndc-usa.com/login",
        "deals_url": "https://www.rndc-usa.com/promotions",
        "selectors": {
            "deal_items": ".promo-item",
            "title": ".promo-name",
            "discount": ".promo-discount",
            "valid_until": ".promo-end-date",
            "price": ".promo-price",
        }
    },
    "glazers": {
        "name": "Southern Glazer's",
        "login_url": "https://www.southernglazers.com/login",
        "deals_url": "https://www.southernglazers.com/deals",
        "selectors": {
            "deal_items": ".deal-item",
            "title": ".deal-title",
            "discount": ".deal-discount",
            "valid_until": ".deal-expires",
            "price": ".deal-price",
        }
    },
    "custom": {
        "name": "Custom Portal",
        "login_url": "",
        "deals_url": "",
        "selectors": {}
    }
}


class SupplierMonitor:
    """
    Monitors supplier portals for deals.
    Uses aiohttp for HTTP requests and BeautifulSoup for parsing.
    
    For full browser-based portals (JS-heavy), upgrade to Playwright.
    """

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": "Mozilla/5.0 (compatible; ZachsLiquorMonitor/1.0)"},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def fetch_deals(self, supplier_config: dict) -> list[dict]:
        """
        Fetch deals from a supplier portal.
        Returns list of deal dicts.
        """
        portal_type = supplier_config.get("portal_type", "custom")
        username = supplier_config.get("portal_username")
        password = supplier_config.get("portal_password")

        if not username or not password:
            logger.warning(f"No credentials for supplier {supplier_config.get('name')}")
            return []

        config = PORTAL_CONFIGS.get(portal_type, PORTAL_CONFIGS["custom"])
        if not config["login_url"] or not config["deals_url"]:
            logger.warning(f"Portal config incomplete for {portal_type}")
            return []

        try:
            # Step 1: Login
            login_payload = {"username": username, "password": password}
            async with self.session.post(config["login_url"], data=login_payload) as resp:
                if resp.status not in (200, 302):
                    logger.error(f"Login failed for {config['name']}: status {resp.status}")
                    return []

            # Step 2: Fetch deals page
            async with self.session.get(config["deals_url"]) as resp:
                if resp.status != 200:
                    logger.error(f"Deals page fetch failed: {resp.status}")
                    return []
                html = await resp.text()

            # Step 3: Parse
            return self._parse_deals(html, config, supplier_config["id"], portal_type)

        except Exception as e:
            logger.error(f"Error fetching deals from {config['name']}: {e}")
            return []

    def _parse_deals(self, html: str, config: dict, supplier_id: int, source: str) -> list[dict]:
        """Parse deal HTML into structured dicts."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        deals = []
        selectors = config.get("selectors", {})
        items_sel = selectors.get("deal_items", ".deal")

        for item in soup.select(items_sel)[:20]:  # limit to 20 deals
            try:
                title_el = item.select_one(selectors.get("title", "h3"))
                disc_el  = item.select_one(selectors.get("discount", ".discount"))
                exp_el   = item.select_one(selectors.get("valid_until", ".expiry"))
                price_el = item.select_one(selectors.get("price", ".price"))

                title = title_el.get_text(strip=True) if title_el else "Deal"
                description = item.get_text(strip=True)[:300]

                # Extract discount percentage
                discount_pct = None
                if disc_el:
                    import re
                    m = re.search(r"(\d+)%", disc_el.get_text())
                    if m:
                        discount_pct = float(m.group(1))

                # Extract price
                deal_price = None
                if price_el:
                    import re
                    m = re.search(r"\$?([\d.]+)", price_el.get_text())
                    if m:
                        deal_price = float(m.group(1))

                deals.append({
                    "supplier_id": supplier_id,
                    "title": title,
                    "description": description,
                    "discount_pct": discount_pct,
                    "deal_price": deal_price,
                    "source": source,
                    "is_active": True,
                    "is_read": False,
                    "raw_data": {"html_snippet": str(item)[:500]},
                })
            except Exception as e:
                logger.warning(f"Failed to parse deal item: {e}")

        return deals

    @staticmethod
    def create_mock_deals(supplier_id: int, supplier_name: str, source: str) -> list[dict]:
        """
        Mock deals for demo/testing when credentials aren't configured.
        Remove this in production.
        """
        import random
        categories = ["Whiskey", "Vodka", "Beer", "Wine", "Tequila", "Rum"]
        brands = ["Jack Daniel's", "Grey Goose", "Corona", "Barefoot", "Patron", "Bacardi"]
        deals = []
        for i in range(random.randint(2, 5)):
            cat = random.choice(categories)
            brand = random.choice(brands)
            disc = random.choice([10, 15, 20, 25])
            deals.append({
                "supplier_id": supplier_id,
                "title": f"{brand} {cat} — {disc}% OFF",
                "description": f"Limited time promotion: {disc}% off all {brand} products. Order by end of month.",
                "discount_pct": float(disc),
                "deal_price": None,
                "source": source,
                "category": cat,
                "is_active": True,
                "is_read": False,
                "valid_until": datetime.utcnow() + timedelta(days=random.randint(7, 30)),
                "raw_data": {"mock": True},
            })
        return deals


async def run_deal_check(db_session, supplier_id: int = None):
    """
    Called by scheduler. Checks all active monitored suppliers (or a specific one).
    Saves new deals to DB and returns count of new deals found.
    """
    from sqlalchemy import select
    from app.models.models import Supplier, SupplierDeal

    result = await db_session.execute(
        select(Supplier).where(
            Supplier.is_active == True,
            Supplier.monitor_deals == True,
            *([Supplier.id == supplier_id] if supplier_id else [])
        )
    )
    suppliers = result.scalars().all()
    total_new = 0

    async with SupplierMonitor() as monitor:
        for supplier in suppliers:
            sup_dict = {
                "id": supplier.id,
                "name": supplier.name,
                "portal_type": supplier.portal_type or "custom",
                "portal_username": supplier.portal_username,
                "portal_password": supplier.portal_password,
                "portal_url": supplier.portal_url,
            }

            if supplier.portal_username and supplier.portal_password:
                deals = await monitor.fetch_deals(sup_dict)
            else:
                # Use mock deals if no credentials
                deals = SupplierMonitor.create_mock_deals(supplier.id, supplier.name, supplier.portal_type or "custom")

            for deal_data in deals:
                # Check if this deal already exists (deduplicate by title)
                existing = await db_session.execute(
                    select(SupplierDeal).where(
                        SupplierDeal.supplier_id == supplier.id,
                        SupplierDeal.title == deal_data["title"],
                        SupplierDeal.is_active == True,
                    )
                )
                if not existing.scalar_one_or_none():
                    deal = SupplierDeal(**{k: v for k, v in deal_data.items() if k in SupplierDeal.__table__.columns.keys()})
                    db_session.add(deal)
                    total_new += 1

            supplier.last_checked = datetime.utcnow()
            await db_session.flush()

    await db_session.commit()
    return total_new
