# 🥃 Zach's Liquor Store — Inventory Management System

## System Architecture

```
Browser (tablet/laptop at counter)
    ↓ HTTPS
Vercel  ──── React Frontend (UI)
    ↓ REST API calls
Railway ──── FastAPI Backend (Python)
    ↓ SQL
Railway ──── PostgreSQL Database (all data, permanent)
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Database** | PostgreSQL (Railway) | All data, permanent cloud storage |
| **Backend** | FastAPI + Python 3.11 | REST API, business logic, analytics |
| **Frontend** | React + Vite + Recharts | Dashboard UI, charts, forms |
| **Auth** | JWT + TOTP/SMS MFA | Secure login, 2-factor authentication |
| **Hosting** | Railway (backend+DB) + Vercel (frontend) | 24/7 cloud hosting |
| **Scheduler** | APScheduler | Automated supplier deal checks |
| **Supplier Monitor** | aiohttp + BeautifulSoup | Scrapes deal pages (Breakthru, RNDC) |

---

## Features

### Inventory Management
- Full CRUD for all products
- Categories: Beer, Hard Liquor, Wine, Hard Cider, Cocktails, Cool Drinks, Cigarettes, E-Cigarettes, Snacks & Chips, Accessories
- Cost price, sell price, AI-predicted optimal price
- Stock levels with color-coded status
- Low stock + out of stock alerts
- Reorder point and quantity management
- Barcode field for future scanner integration

### Sales
- Record multi-item sales
- Auto-deducts stock on sale
- Revenue, cost, profit tracked per transaction
- Reverse/delete sales (restores stock)

### Expenses
- Full expense tracking with categories
- Recurring expenses (weekly/monthly/yearly)
- Monthly charts and category breakdown

### Analytics (Power BI-style)
- **Daily** view: last 7/14/30/60/90 days
- **Monthly** view: all months, current year filter
- **Yearly** view: year-over-year totals
- **P&L Statement**: Revenue, COGS, Gross Profit, Expenses, Net Profit by month
- **Best sellers**: by units, revenue, or profit
- **Worst/slowest sellers**: identify dead stock
- **Seasonal YoY**: Christmas, New Year's, St. Patrick's Day, Super Bowl, 4th of July, Labor Day, Thanksgiving, Halloween, Cinco de Mayo, Easter, Memorial Day

### Security
- JWT access tokens (1 hour) + refresh tokens (7 days)
- TOTP MFA (Google Authenticator / Authy)
- SMS MFA (via Twilio)
- Backup codes (8 one-time codes)
- Login lockout after 5 failed attempts (15 min)
- Password strength validation
- Full audit log

### Supplier Deal Monitoring
- Monitors Breakthru Beverage, RNDC portals
- Configurable for any additional portal
- Automatic hourly checks (configurable)
- In-app notification panel with unread badge
- Manual "Check Now" trigger

---

## Quick Start (Local)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (local or cloud)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY
uvicorn main:app --reload
```
API docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
# VITE_API_URL=http://localhost:8000
npm run dev
```
App: http://localhost:5173

### Seed database
```bash
cd backend
python seed.py
```
This creates: admin (zach/Zach1234!), staff account, all products/categories/suppliers, 6 months historical sales.

---

## Deployment

### Step 1: Push to GitHub
```bash
git init && git add . && git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/zachs-liquor.git
git push -u origin main
```

### Step 2: Deploy Backend on Railway
1. railway.app → New Project → Deploy from GitHub → select `backend/` folder
2. Add PostgreSQL: New → Database → Add PostgreSQL
3. Set environment variables:
   ```
   DATABASE_URL   = (Railway auto-fills from PostgreSQL service)
   SECRET_KEY     = (generate: python -c "import secrets; print(secrets.token_hex(32))")
   ENVIRONMENT    = production
   FRONTEND_URL   = https://your-app.vercel.app
   ```
4. Open Railway shell → `python seed.py`
5. Your API: https://your-app.railway.app

### Step 3: Deploy Frontend on Vercel
1. vercel.com → New Project → import GitHub repo
2. Root Directory: `frontend/`
3. Framework: Vite
4. Environment variable: `VITE_API_URL=https://your-app.railway.app`
5. Deploy → https://zachs-liquor.vercel.app

---

## Supplier Deal Monitoring Setup

1. Go to Settings → Suppliers
2. Edit a supplier
3. Set Portal Type: `breakthru`, `rndc`, `glazers`, or `custom`
4. Enter Portal Username and Password (your login for that site)
5. Enable "Monitor Deals" toggle
6. Deals will be checked every 60 minutes automatically
7. Click "Check Now" in the Deals tab to run immediately

**Supported portals out of the box:**
- Breakthru Beverage (breakthrubev.com)
- RNDC (rndc-usa.com)
- Southern Glazer's (southernglazers.com)

**To add a new supplier portal:** Edit `backend/app/services/supplier_monitor.py` → add entry to `PORTAL_CONFIGS` with login URL, deals URL, and CSS selectors.

---

## MFA Setup (for Zach)

After first login:
1. Go to Settings
2. Click "Enable Authenticator App"
3. Scan QR code with Google Authenticator or Authy
4. Enter the 6-digit code to confirm
5. Save your 8 backup codes somewhere safe

Or use SMS:
1. Click "Enable SMS MFA"
2. Enter your phone number
3. Enter the verification code received

---

## POS Integration

The app works as a standalone POS:
- Open in browser on tablet/laptop at counter
- Record sales tab → add items → complete

To connect to Square/Clover POS later:
- Add a webhook endpoint to the backend (template ready in `app/routers/`)
- Configure the POS to send webhooks to `https://your-app.railway.app/webhooks/square`
- Sales will auto-sync without manual entry

---

## Costs

| Service | Plan | Cost |
|---|---|---|
| Railway (backend + PostgreSQL) | Hobby | ~$5/month |
| Vercel (frontend) | Free | $0 |
| Twilio (SMS MFA, optional) | Pay-as-you-go | ~$0.01/SMS |
| **Total** | | ~$5/month |

---

## Project Structure

```
zachs-liquor-store/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # All settings
│   │   │   └── security.py        # JWT, MFA, passwords
│   │   ├── models/
│   │   │   └── models.py          # All DB tables
│   │   ├── routers/
│   │   │   ├── auth.py            # Login, MFA, register
│   │   │   ├── analytics.py       # All analytics endpoints
│   │   │   └── products_expenses.py # Products, expenses, deals
│   │   ├── services/
│   │   │   ├── pricing.py         # AI price prediction
│   │   │   ├── seasonal.py        # Holiday YoY logic
│   │   │   └── supplier_monitor.py # Deal scraping
│   │   └── database.py            # DB connection
│   ├── main.py                    # App entry + scheduler
│   ├── seed.py                    # DB seed data
│   ├── requirements.txt
│   ├── Procfile                   # Railway start command
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx  # Main KPI dashboard
│   │   │   ├── InventoryPage.jsx  # Full product CRUD
│   │   │   ├── SalesPage.jsx      # Record + view sales
│   │   │   ├── ExpensesPage.jsx   # Expense tracking
│   │   │   ├── AnalyticsPage.jsx  # Daily/monthly/yearly/P&L
│   │   │   ├── SeasonalPage.jsx   # Holiday YoY comparison
│   │   │   ├── AlertsPage.jsx     # Stock alerts
│   │   │   ├── DealsPage.jsx      # Supplier deals
│   │   │   ├── SettingsPage.jsx   # MFA, account, config
│   │   │   └── LoginPage.jsx      # Login + MFA step 2
│   │   ├── components/
│   │   │   ├── layout/Layout.jsx  # Sidebar + navigation
│   │   │   └── ui.jsx             # Shared components
│   │   ├── services/api.js        # All API calls
│   │   ├── store/authStore.js     # Auth state
│   │   └── App.jsx                # Routes
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── README.md
```
