"""
Zach's Liquor Store — Database Seed Script
Run ONCE after first deploy to populate the database.

Usage:
    cd backend
    python seed.py
"""
import asyncio
import random
from datetime import datetime, timedelta
from app.database import AsyncSessionLocal, create_tables
from app.models.models import (
    User, Category, Supplier, Product,
    Sale, SaleItem, Expense, ExpenseCategory, SupplierDeal
)
from app.core.security import hash_password


# ── Categories ────────────────────────────────────────────────────────────────
CATEGORIES = [
    {"name": "Beer",            "description": "Domestic, imported, craft, hard seltzer",          "color": "#378ADD"},
    {"name": "Hard Liquor",     "description": "Whiskey, Vodka, Tequila, Rum, Gin, Bourbon",       "color": "#BA7517"},
    {"name": "Wine",            "description": "Red, white, rosé, sparkling, dessert",             "color": "#D4537E"},
    {"name": "Hard Cider",      "description": "Apple, pear, and flavored alcoholic ciders",       "color": "#639922"},
    {"name": "Cocktails",       "description": "RTD cocktails, canned cocktails, mixers",          "color": "#534AB7"},
    {"name": "Cool Drinks",     "description": "Non-alcoholic: sodas, energy drinks, juices",      "color": "#0F6E56"},
    {"name": "Cigarettes",      "description": "Cigarettes and tobacco products",                  "color": "#888780"},
    {"name": "E-Cigarettes",    "description": "Vapes, disposables, pods, starter kits",           "color": "#5588CC"},
    {"name": "Snacks & Chips",  "description": "Chips, nuts, jerky, candy, snack foods",           "color": "#E24B4A"},
    {"name": "Accessories",     "description": "Ice, cups, openers, lighters, misc items",         "color": "#d4af37"},
]

# ── Expense Categories ────────────────────────────────────────────────────────
EXPENSE_CATEGORIES = [
    {"name": "Rent",        "color": "#E24B4A"},
    {"name": "Utilities",   "color": "#BA7517"},
    {"name": "Payroll",     "color": "#378ADD"},
    {"name": "Insurance",   "color": "#534AB7"},
    {"name": "Supplies",    "color": "#639922"},
    {"name": "Marketing",   "color": "#D4537E"},
    {"name": "Maintenance", "color": "#888780"},
    {"name": "Licenses",    "color": "#d4af37"},
    {"name": "Other",       "color": "#aaaaaa"},
]

# ── Suppliers ─────────────────────────────────────────────────────────────────
SUPPLIERS = [
    {"name": "Brown-Forman Beverages",  "contact_email": "orders@brown-forman.com",   "phone": "502-585-1100", "lead_days": 3,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "Bacardi USA",             "contact_email": "orders@bacardi.com",         "phone": "305-573-8511", "lead_days": 5,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "LVMH Wines & Spirits",    "contact_email": "orders@lvmh.com",            "phone": "212-931-2240", "lead_days": 7,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "AB InBev Distributors",   "contact_email": "orders@ab-inbev.com",        "phone": "314-577-2000", "lead_days": 2,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "Pernod Ricard USA",       "contact_email": "orders@pernod-ricard.com",   "phone": "212-372-5400", "lead_days": 4,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "Fifth Generation Inc.",   "contact_email": "orders@titosvodka.com",      "phone": "512-928-9134", "lead_days": 3,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "Diageo North America",    "contact_email": "orders@diageo.com",          "phone": "212-805-4000", "lead_days": 5,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "Constellation Brands",    "contact_email": "orders@cbrands.com",         "phone": "585-678-7100", "lead_days": 4,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "Breakthru Beverage",      "contact_email": "orders@breakthrubev.com",    "phone": "847-325-3000", "lead_days": 3,  "portal_type": "breakthru", "monitor_deals": True,
     "portal_url": "https://www.breakthrubev.com"},
    {"name": "RNDC",                    "contact_email": "orders@rndc-usa.com",        "phone": "214-550-2000", "lead_days": 3,  "portal_type": "rndc",      "monitor_deals": True,
     "portal_url": "https://www.rndc-usa.com"},
    {"name": "Southern Glazer's Wine",  "contact_email": "orders@southernglazers.com", "phone": "305-625-4171", "lead_days": 3,  "portal_type": "glazers",   "monitor_deals": True,
     "portal_url": "https://www.southernglazers.com"},
    {"name": "Philip Morris USA",       "contact_email": "orders@pm.com",              "phone": "804-274-2000", "lead_days": 5,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "R.J. Reynolds",           "contact_email": "orders@rjrt.com",            "phone": "336-741-5000", "lead_days": 5,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "Altria Group",            "contact_email": "orders@altria.com",          "phone": "804-274-7000", "lead_days": 5,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "PepsiCo Snacks",          "contact_email": "snacks@pepsico.com",         "phone": "914-253-2000", "lead_days": 2,  "portal_type": "custom",    "monitor_deals": False},
    {"name": "Local Ice Supplier",      "contact_email": "info@localice.com",          "phone": "555-100-2000", "lead_days": 1,  "portal_type": "custom",    "monitor_deals": False},
]

# ── Products ──────────────────────────────────────────────────────────────────
PRODUCTS = [
    # BEER
    {"name": "Bud Light 12-Pack",           "sku": "BL-12PK",    "category": "Beer",           "subcategory": "Domestic",      "unit": "12-pack cans", "cost_price": 9.50,  "sell_price": 15.99, "stock": 80,  "reorder_point": 24, "reorder_qty": 48, "supplier": "AB InBev Distributors"},
    {"name": "Budweiser 12-Pack",           "sku": "BUD-12PK",   "category": "Beer",           "subcategory": "Domestic",      "unit": "12-pack cans", "cost_price": 9.50,  "sell_price": 15.99, "stock": 60,  "reorder_point": 24, "reorder_qty": 48, "supplier": "AB InBev Distributors"},
    {"name": "Corona Extra 12-Pack",        "sku": "COR-12PK",   "category": "Beer",           "subcategory": "Imported",      "unit": "12-pack btls", "cost_price": 12.50, "sell_price": 19.99, "stock": 72,  "reorder_point": 24, "reorder_qty": 48, "supplier": "Constellation Brands"},
    {"name": "Modelo Especial 12-Pack",     "sku": "MOD-12PK",   "category": "Beer",           "subcategory": "Imported",      "unit": "12-pack cans", "cost_price": 12.00, "sell_price": 18.99, "stock": 84,  "reorder_point": 24, "reorder_qty": 48, "supplier": "Constellation Brands"},
    {"name": "Heineken 6-Pack",             "sku": "HEI-6PK",    "category": "Beer",           "subcategory": "Imported",      "unit": "6-pack btls",  "cost_price": 7.00,  "sell_price": 11.99, "stock": 48,  "reorder_point": 12, "reorder_qty": 24, "supplier": "AB InBev Distributors"},
    {"name": "Blue Moon 6-Pack",            "sku": "BLM-6PK",    "category": "Beer",           "subcategory": "Craft",         "unit": "6-pack btls",  "cost_price": 7.50,  "sell_price": 12.99, "stock": 36,  "reorder_point": 12, "reorder_qty": 24, "supplier": "AB InBev Distributors"},
    {"name": "White Claw Variety 12-Pack",  "sku": "WCL-12PK",   "category": "Beer",           "subcategory": "Hard Seltzer",  "unit": "12-pack",      "cost_price": 13.00, "sell_price": 20.99, "stock": 50,  "reorder_point": 12, "reorder_qty": 24, "supplier": "AB InBev Distributors"},
    {"name": "Truly Hard Seltzer 12-Pack",  "sku": "TRU-12PK",   "category": "Beer",           "subcategory": "Hard Seltzer",  "unit": "12-pack",      "cost_price": 13.00, "sell_price": 19.99, "stock": 40,  "reorder_point": 12, "reorder_qty": 24, "supplier": "Breakthru Beverage"},
    # HARD LIQUOR
    {"name": "Jack Daniel's 750ml",         "sku": "JDW-750",    "category": "Hard Liquor",    "subcategory": "Whiskey",       "unit": "750ml",        "cost_price": 18.50, "sell_price": 32.99, "stock": 48,  "reorder_point": 12, "reorder_qty": 24, "supplier": "Brown-Forman Beverages"},
    {"name": "Jack Daniel's 1.75L",         "sku": "JDW-1750",   "category": "Hard Liquor",    "subcategory": "Whiskey",       "unit": "1.75L",        "cost_price": 34.00, "sell_price": 57.99, "stock": 18,  "reorder_point": 6,  "reorder_qty": 12, "supplier": "Brown-Forman Beverages"},
    {"name": "Jameson Irish Whiskey 750ml", "sku": "JAM-750",    "category": "Hard Liquor",    "subcategory": "Whiskey",       "unit": "750ml",        "cost_price": 16.00, "sell_price": 28.99, "stock": 7,   "reorder_point": 10, "reorder_qty": 24, "supplier": "Pernod Ricard USA"},
    {"name": "Woodford Reserve Bourbon",    "sku": "WFR-750",    "category": "Hard Liquor",    "subcategory": "Bourbon",       "unit": "750ml",        "cost_price": 24.00, "sell_price": 42.99, "stock": 22,  "reorder_point": 8,  "reorder_qty": 12, "supplier": "Brown-Forman Beverages"},
    {"name": "Hennessy VS Cognac 750ml",    "sku": "HEN-VS-750", "category": "Hard Liquor",    "subcategory": "Cognac",        "unit": "750ml",        "cost_price": 28.00, "sell_price": 52.99, "stock": 24,  "reorder_point": 8,  "reorder_qty": 12, "supplier": "LVMH Wines & Spirits"},
    {"name": "Grey Goose Vodka 750ml",      "sku": "GGV-750",    "category": "Hard Liquor",    "subcategory": "Vodka",         "unit": "750ml",        "cost_price": 22.00, "sell_price": 42.99, "stock": 6,   "reorder_point": 10, "reorder_qty": 24, "supplier": "Bacardi USA"},
    {"name": "Tito's Handmade Vodka 750ml", "sku": "TIT-750",    "category": "Hard Liquor",    "subcategory": "Vodka",         "unit": "750ml",        "cost_price": 14.00, "sell_price": 26.99, "stock": 55,  "reorder_point": 15, "reorder_qty": 36, "supplier": "Fifth Generation Inc."},
    {"name": "Absolut Vodka 750ml",         "sku": "ABS-750",    "category": "Hard Liquor",    "subcategory": "Vodka",         "unit": "750ml",        "cost_price": 12.50, "sell_price": 22.99, "stock": 40,  "reorder_point": 12, "reorder_qty": 24, "supplier": "Pernod Ricard USA"},
    {"name": "Don Julio Blanco 750ml",      "sku": "DJT-BL-750", "category": "Hard Liquor",    "subcategory": "Tequila",       "unit": "750ml",        "cost_price": 38.00, "sell_price": 68.99, "stock": 18,  "reorder_point": 6,  "reorder_qty": 12, "supplier": "Diageo North America"},
    {"name": "Patron Silver Tequila 750ml", "sku": "PAT-SIL-750","category": "Hard Liquor",    "subcategory": "Tequila",       "unit": "750ml",        "cost_price": 32.00, "sell_price": 58.99, "stock": 14,  "reorder_point": 6,  "reorder_qty": 12, "supplier": "Bacardi USA"},
    {"name": "Bacardi Superior Rum 750ml",  "sku": "BAC-WR-750", "category": "Hard Liquor",    "subcategory": "Rum",           "unit": "750ml",        "cost_price": 10.00, "sell_price": 18.99, "stock": 3,   "reorder_point": 12, "reorder_qty": 24, "supplier": "Bacardi USA"},
    {"name": "Captain Morgan Spiced 750ml", "sku": "CAP-750",    "category": "Hard Liquor",    "subcategory": "Rum",           "unit": "750ml",        "cost_price": 11.00, "sell_price": 20.99, "stock": 0,   "reorder_point": 10, "reorder_qty": 24, "supplier": "Diageo North America"},
    {"name": "Tanqueray London Gin 750ml",  "sku": "TAN-750",    "category": "Hard Liquor",    "subcategory": "Gin",           "unit": "750ml",        "cost_price": 15.00, "sell_price": 27.99, "stock": 20,  "reorder_point": 8,  "reorder_qty": 12, "supplier": "Diageo North America"},
    # WINE
    {"name": "Barefoot Merlot 750ml",       "sku": "BFM-750",    "category": "Wine",           "subcategory": "Red",           "unit": "750ml",        "cost_price": 5.50,  "sell_price": 10.99, "stock": 36,  "reorder_point": 12, "reorder_qty": 24, "supplier": "Southern Glazer's Wine"},
    {"name": "Barefoot Chardonnay 750ml",   "sku": "BFC-750",    "category": "Wine",           "subcategory": "White",         "unit": "750ml",        "cost_price": 5.50,  "sell_price": 10.99, "stock": 30,  "reorder_point": 12, "reorder_qty": 24, "supplier": "Southern Glazer's Wine"},
    {"name": "Meiomi Pinot Noir 750ml",     "sku": "MEI-750",    "category": "Wine",           "subcategory": "Red",           "unit": "750ml",        "cost_price": 9.00,  "sell_price": 17.99, "stock": 20,  "reorder_point": 8,  "reorder_qty": 12, "supplier": "Southern Glazer's Wine"},
    {"name": "Kim Crawford Sauv Blanc",     "sku": "KCS-750",    "category": "Wine",           "subcategory": "White",         "unit": "750ml",        "cost_price": 10.00, "sell_price": 18.99, "stock": 18,  "reorder_point": 8,  "reorder_qty": 12, "supplier": "Breakthru Beverage"},
    {"name": "Moet Chandon Brut 750ml",     "sku": "MOE-750",    "category": "Wine",           "subcategory": "Sparkling",     "unit": "750ml",        "cost_price": 32.00, "sell_price": 54.99, "stock": 10,  "reorder_point": 4,  "reorder_qty": 6,  "supplier": "LVMH Wines & Spirits"},
    # HARD CIDER
    {"name": "Angry Orchard Crisp 6-Pack",  "sku": "ANG-6PK",    "category": "Hard Cider",     "subcategory": "Apple",         "unit": "6-pack btls",  "cost_price": 7.00,  "sell_price": 11.99, "stock": 30,  "reorder_point": 10, "reorder_qty": 24, "supplier": "AB InBev Distributors"},
    {"name": "Strongbow Gold Apple 6-Pack", "sku": "STR-6PK",    "category": "Hard Cider",     "subcategory": "Apple",         "unit": "6-pack cans",  "cost_price": 6.50,  "sell_price": 10.99, "stock": 24,  "reorder_point": 8,  "reorder_qty": 24, "supplier": "AB InBev Distributors"},
    # COCKTAILS / RTD
    {"name": "High Noon Vodka Soda 8-Pack", "sku": "HNV-8PK",    "category": "Cocktails",      "subcategory": "RTD",           "unit": "8-pack cans",  "cost_price": 12.00, "sell_price": 19.99, "stock": 36,  "reorder_point": 12, "reorder_qty": 24, "supplier": "Constellation Brands"},
    {"name": "Cutwater Margarita 4-Pack",   "sku": "CTM-4PK",    "category": "Cocktails",      "subcategory": "Canned",        "unit": "4-pack cans",  "cost_price": 8.00,  "sell_price": 14.99, "stock": 28,  "reorder_point": 8,  "reorder_qty": 24, "supplier": "Constellation Brands"},
    {"name": "Jose Cuervo Margarita Mix",   "sku": "JCM-1L",     "category": "Cocktails",      "subcategory": "Mixer",         "unit": "1L bottle",    "cost_price": 4.00,  "sell_price": 7.99,  "stock": 24,  "reorder_point": 8,  "reorder_qty": 24, "supplier": "Diageo North America"},
    # COOL DRINKS
    {"name": "Coca-Cola 6-Pack",            "sku": "COK-6PK",    "category": "Cool Drinks",    "subcategory": "Soda",          "unit": "6-pack cans",  "cost_price": 3.50,  "sell_price": 5.99,  "stock": 48,  "reorder_point": 12, "reorder_qty": 48, "supplier": "Southern Glazer's Wine"},
    {"name": "Sprite 6-Pack",               "sku": "SPR-6PK",    "category": "Cool Drinks",    "subcategory": "Soda",          "unit": "6-pack cans",  "cost_price": 3.50,  "sell_price": 5.99,  "stock": 36,  "reorder_point": 12, "reorder_qty": 48, "supplier": "Southern Glazer's Wine"},
    {"name": "Red Bull 4-Pack",             "sku": "RBL-4PK",    "category": "Cool Drinks",    "subcategory": "Energy",        "unit": "4-pack cans",  "cost_price": 6.50,  "sell_price": 10.99, "stock": 36,  "reorder_point": 12, "reorder_qty": 24, "supplier": "Southern Glazer's Wine"},
    {"name": "Tonic Water 4-Pack",          "sku": "TON-4PK",    "category": "Cool Drinks",    "subcategory": "Mixer",         "unit": "4-pack btls",  "cost_price": 3.00,  "sell_price": 5.49,  "stock": 20,  "reorder_point": 8,  "reorder_qty": 24, "supplier": "Southern Glazer's Wine"},
    # CIGARETTES
    {"name": "Marlboro Red Pack",           "sku": "MAR-RED",    "category": "Cigarettes",     "subcategory": "Regular",       "unit": "pack",         "cost_price": 6.50,  "sell_price": 10.99, "stock": 5,   "reorder_point": 20, "reorder_qty": 50, "supplier": "Philip Morris USA"},
    {"name": "Newport Menthol Pack",        "sku": "NEW-MEN",    "category": "Cigarettes",     "subcategory": "Menthol",       "unit": "pack",         "cost_price": 6.80,  "sell_price": 11.49, "stock": 8,   "reorder_point": 20, "reorder_qty": 50, "supplier": "R.J. Reynolds"},
    {"name": "Marlboro Lights Pack",        "sku": "MAR-LGT",    "category": "Cigarettes",     "subcategory": "Light",         "unit": "pack",         "cost_price": 6.50,  "sell_price": 10.99, "stock": 0,   "reorder_point": 20, "reorder_qty": 50, "supplier": "Philip Morris USA"},
    {"name": "Camel Blue Pack",             "sku": "CAM-BLU",    "category": "Cigarettes",     "subcategory": "Regular",       "unit": "pack",         "cost_price": 6.60,  "sell_price": 11.29, "stock": 12,  "reorder_point": 20, "reorder_qty": 50, "supplier": "R.J. Reynolds"},
    # E-CIGARETTES
    {"name": "JUUL Starter Kit",            "sku": "JUL-KIT",    "category": "E-Cigarettes",   "subcategory": "Starter Kit",   "unit": "kit",          "cost_price": 12.00, "sell_price": 19.99, "stock": 14,  "reorder_point": 6,  "reorder_qty": 12, "supplier": "Altria Group"},
    {"name": "Vuse Alto Pod 2-Pack",        "sku": "VUS-POD",    "category": "E-Cigarettes",   "subcategory": "Pod",           "unit": "2-pack",       "cost_price": 5.00,  "sell_price": 8.99,  "stock": 22,  "reorder_point": 10, "reorder_qty": 24, "supplier": "R.J. Reynolds"},
    {"name": "Breeze Plus Disposable",      "sku": "BRZ-DISP",   "category": "E-Cigarettes",   "subcategory": "Disposable",    "unit": "each",         "cost_price": 6.00,  "sell_price": 10.99, "stock": 30,  "reorder_point": 10, "reorder_qty": 30, "supplier": "Altria Group"},
    # SNACKS & CHIPS
    {"name": "Lays Classic Chips",          "sku": "LAY-REG",    "category": "Snacks & Chips", "subcategory": "Chips",         "unit": "bag",          "cost_price": 1.20,  "sell_price": 2.99,  "stock": 60,  "reorder_point": 24, "reorder_qty": 48, "supplier": "PepsiCo Snacks"},
    {"name": "Doritos Nacho Cheese",        "sku": "DOR-NAC",    "category": "Snacks & Chips", "subcategory": "Chips",         "unit": "bag",          "cost_price": 1.20,  "sell_price": 2.99,  "stock": 45,  "reorder_point": 24, "reorder_qty": 48, "supplier": "PepsiCo Snacks"},
    {"name": "Planters Peanuts",            "sku": "PLN-PNT",    "category": "Snacks & Chips", "subcategory": "Nuts",          "unit": "can",          "cost_price": 1.50,  "sell_price": 3.49,  "stock": 30,  "reorder_point": 12, "reorder_qty": 24, "supplier": "PepsiCo Snacks"},
    {"name": "Jack Link's Beef Jerky",      "sku": "JLK-BEF",    "category": "Snacks & Chips", "subcategory": "Jerky",         "unit": "bag",          "cost_price": 2.50,  "sell_price": 4.99,  "stock": 24,  "reorder_point": 10, "reorder_qty": 24, "supplier": "PepsiCo Snacks"},
    # ACCESSORIES
    {"name": "Bag of Ice 5lb",              "sku": "ICE-5LB",    "category": "Accessories",    "subcategory": "Ice",           "unit": "5 lb bag",     "cost_price": 0.80,  "sell_price": 2.99,  "stock": 100, "reorder_point": 30, "reorder_qty": 100,"supplier": "Local Ice Supplier"},
    {"name": "Solo Cups 18-Pack",           "sku": "CUP-18PK",   "category": "Accessories",    "subcategory": "Cups",          "unit": "18-pack",      "cost_price": 2.50,  "sell_price": 5.99,  "stock": 40,  "reorder_point": 10, "reorder_qty": 24, "supplier": "Local Ice Supplier"},
    {"name": "Bic Lighter",                 "sku": "BIC-LGT",    "category": "Accessories",    "subcategory": "Lighter",       "unit": "each",         "cost_price": 0.50,  "sell_price": 1.99,  "stock": 80,  "reorder_point": 20, "reorder_qty": 50, "supplier": "Local Ice Supplier"},
]

SAMPLE_EXPENSES = [
    {"title": "Monthly Rent",       "amount": 3500.00, "cat": "Rent",        "vendor": "Property Management", "is_recurring": True,  "recurrence": "monthly"},
    {"title": "Electricity Bill",   "amount": 420.00,  "cat": "Utilities",   "vendor": "City Electric",       "is_recurring": True,  "recurrence": "monthly"},
    {"title": "Water & Sewer",      "amount": 85.00,   "cat": "Utilities",   "vendor": "City Water",          "is_recurring": True,  "recurrence": "monthly"},
    {"title": "Employee Payroll",   "amount": 4800.00, "cat": "Payroll",     "vendor": "Internal",            "is_recurring": True,  "recurrence": "monthly"},
    {"title": "Liability Insurance","amount": 280.00,  "cat": "Insurance",   "vendor": "State Farm",          "is_recurring": True,  "recurrence": "monthly"},
    {"title": "Store Supplies",     "amount": 120.00,  "cat": "Supplies",    "vendor": "Office Depot",        "is_recurring": False, "recurrence": None},
    {"title": "Liquor License Renewal","amount":800.00,"cat": "Licenses",    "vendor": "State ABC Board",     "is_recurring": True,  "recurrence": "yearly"},
    {"title": "POS System Fee",     "amount": 49.00,   "cat": "Supplies",    "vendor": "Square Inc.",         "is_recurring": True,  "recurrence": "monthly"},
    {"title": "Refrigerator Repair","amount": 350.00,  "cat": "Maintenance", "vendor": "HVAC Pro",            "is_recurring": False, "recurrence": None},
    {"title": "Social Media Ads",   "amount": 200.00,  "cat": "Marketing",   "vendor": "Meta Ads",            "is_recurring": True,  "recurrence": "monthly"},
]


async def seed():
    print("🥃 Seeding Zach's Liquor Store database...")
    await create_tables()

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # ── Users ──────────────────────────────────────────────────────────────
        existing = await db.execute(select(User).where(User.username == "zach"))
        if not existing.scalar_one_or_none():
            db.add(User(
                username="zach", email="zach@zachsliquor.com",
                hashed_password=hash_password("Zach1234!"),
                full_name="Zach (Owner)", is_admin=True,
            ))
            await db.flush()
            print("  ✓ Owner account: zach / Zach1234!")

        existing = await db.execute(select(User).where(User.username == "staff"))
        if not existing.scalar_one_or_none():
            db.add(User(
                username="staff", email="staff@zachsliquor.com",
                hashed_password=hash_password("Staff123!"),
                full_name="Store Staff", is_admin=False,
            ))
            await db.flush()
            print("  ✓ Staff account: staff / Staff123!")

        # ── Categories ──────────────────────────────────────────────────────────
        for cat_data in CATEGORIES:
            r = await db.execute(select(Category).where(Category.name == cat_data["name"]))
            if not r.scalar_one_or_none():
                db.add(Category(**cat_data))
        await db.flush()
        print(f"  ✓ {len(CATEGORIES)} product categories created")

        # ── Expense Categories ─────────────────────────────────────────────────
        for ec in EXPENSE_CATEGORIES:
            r = await db.execute(select(ExpenseCategory).where(ExpenseCategory.name == ec["name"]))
            if not r.scalar_one_or_none():
                db.add(ExpenseCategory(**ec))
        await db.flush()
        print(f"  ✓ {len(EXPENSE_CATEGORIES)} expense categories created")

        # ── Suppliers ──────────────────────────────────────────────────────────
        supplier_map = {}
        for s_data in SUPPLIERS:
            r = await db.execute(select(Supplier).where(Supplier.name == s_data["name"]))
            sup = r.scalar_one_or_none()
            if not sup:
                sup = Supplier(**s_data)
                db.add(sup)
                await db.flush()
            supplier_map[s_data["name"]] = sup.id
        print(f"  ✓ {len(SUPPLIERS)} suppliers created")

        # ── Products ───────────────────────────────────────────────────────────
        from app.services.pricing import predict_price
        product_ids = []
        created_count = 0
        for p_data in PRODUCTS:
            supplier_name = p_data.pop("supplier")
            r = await db.execute(select(Product).where(Product.sku == p_data["sku"]))
            prod = r.scalar_one_or_none()
            if not prod:
                p_data["supplier_id"] = supplier_map.get(supplier_name)
                pred = predict_price(p_data["cost_price"], p_data["category"], p_data["sell_price"])
                p_data["predicted_price"] = pred["predicted_price"]
                p_data["min_price"] = pred["min_price"]
                prod = Product(**p_data)
                db.add(prod)
                await db.flush()
                created_count += 1
            product_ids.append((prod.id, prod.sell_price, prod.cost_price))
        print(f"  ✓ {created_count} products created ({len(product_ids)} total)")

        # ── Historical Sales — 6 months ────────────────────────────────────────
        admin_r = await db.execute(select(User).where(User.username == "zach"))
        admin = admin_r.scalar_one()

        existing_sales = await db.execute(select(Sale))
        if not existing_sales.scalars().first():
            sales_created = 0
            for days_ago in range(180, 0, -1):
                n_sales = random.randint(2, 8)
                for _ in range(n_sales):
                    num_items = random.randint(1, 5)
                    selected = random.sample(product_ids, min(num_items, len(product_ids)))
                    items_data, total_rev, total_cost = [], 0.0, 0.0
                    for pid, sell_p, cost_p in selected:
                        qty = random.randint(1, 6)
                        sub = round(qty * sell_p, 2)
                        cst = round(qty * cost_p, 2)
                        total_rev += sub; total_cost += cst
                        items_data.append({"product_id": pid, "quantity": qty, "unit_cost": cost_p, "unit_price": sell_p, "subtotal": sub, "profit": round(sub - cst, 2)})
                    sale = Sale(
                        sale_date=datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(8, 22), minutes=random.randint(0, 59)),
                        total_revenue=round(total_rev, 2), total_cost=round(total_cost, 2),
                        total_profit=round(total_rev - total_cost, 2),
                        payment_method=random.choice(["cash", "card", "cash", "card", "cash"]),
                        created_by=admin.id,
                    )
                    db.add(sale)
                    await db.flush()
                    for item in items_data:
                        db.add(SaleItem(sale_id=sale.id, **item))
                    sales_created += 1
            print(f"  ✓ {sales_created} historical sales created (6 months)")

        # ── Expenses — 6 months ────────────────────────────────────────────────
        existing_exp = await db.execute(select(Expense))
        if not existing_exp.scalars().first():
            exp_cat_map = {}
            for ec in EXPENSE_CATEGORIES:
                r = await db.execute(select(ExpenseCategory).where(ExpenseCategory.name == ec["name"]))
                ec_obj = r.scalar_one_or_none()
                if ec_obj:
                    exp_cat_map[ec["name"]] = ec_obj.id

            exp_count = 0
            for months_ago in range(6, 0, -1):
                exp_date = datetime.utcnow() - timedelta(days=months_ago * 30)
                for e_data in SAMPLE_EXPENSES:
                    if not e_data["is_recurring"] and months_ago > 1:
                        continue
                    db.add(Expense(
                        title=e_data["title"],
                        amount=e_data["amount"] * random.uniform(0.9, 1.1),
                        category_id=exp_cat_map.get(e_data["cat"]),
                        expense_date=exp_date + timedelta(days=random.randint(0, 5)),
                        vendor=e_data["vendor"],
                        is_recurring=e_data["is_recurring"],
                        recurrence=e_data["recurrence"],
                        created_by=admin.id,
                    ))
                    exp_count += 1
            print(f"  ✓ {exp_count} expense records created")

        # ── Sample Supplier Deals ──────────────────────────────────────────────
        existing_deals = await db.execute(select(SupplierDeal))
        if not existing_deals.scalars().first():
            breakthru_id = supplier_map.get("Breakthru Beverage")
            rndc_id = supplier_map.get("RNDC")
            if breakthru_id:
                for title, disc, cat in [
                    ("Tito's Vodka 20% OFF — Limited Time", 20, "Hard Liquor"),
                    ("Truly Hard Seltzer Case Deal — Buy 2 Get 1", 33, "Beer"),
                    ("Kim Crawford Wine Portfolio Sale — 15% OFF", 15, "Wine"),
                ]:
                    db.add(SupplierDeal(supplier_id=breakthru_id, title=title, discount_pct=disc, category=cat,
                                        description=f"Promotional pricing available this month. Contact rep to place order.",
                                        source="breakthru", is_read=False, is_active=True,
                                        valid_until=datetime.utcnow() + timedelta(days=14)))
            if rndc_id:
                for title, disc, cat in [
                    ("Jack Daniel's Holiday Bundle — 18% OFF", 18, "Hard Liquor"),
                    ("Modelo 24-Pack Promo — $3 OFF per case", 12, "Beer"),
                ]:
                    db.add(SupplierDeal(supplier_id=rndc_id, title=title, discount_pct=disc, category=cat,
                                        description=f"End of month promotion. Valid while supplies last.",
                                        source="rndc", is_read=False, is_active=True,
                                        valid_until=datetime.utcnow() + timedelta(days=7)))
            print("  ✓ 5 sample supplier deals created")

        await db.commit()
        print("\n✅ Zach's Liquor Store is ready!")
        print("   Owner  → username: zach     password: Zach1234!")
        print("   Staff  → username: staff    password: Staff123!")
        print("   API docs → http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
