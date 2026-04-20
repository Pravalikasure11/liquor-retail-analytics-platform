"""
Zach's Liquor Store — Basic API Tests
Run with: pytest tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

import os
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENVIRONMENT"] = "test"

from main import app
from app.database import get_db, Base

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    """Create user and return auth headers."""
    await client.post("/auth/register", json={
        "username": "testuser", "email": "test@test.com",
        "password": "Test1234!", "is_admin": True
    })
    resp = await client.post("/auth/login", json={"username": "testuser", "password": "Test1234!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/auth/register", json={
        "username": "newuser", "email": "new@test.com", "password": "New1234!"
    })
    assert resp.status_code == 201
    assert resp.json()["username"] == "newuser"


@pytest.mark.asyncio
async def test_register_weak_password(client):
    resp = await client.post("/auth/register", json={
        "username": "user2", "email": "u2@test.com", "password": "weak"
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/auth/register", json={
        "username": "loginuser", "email": "login@test.com", "password": "Login1234!"
    })
    resp = await client.post("/auth/login", json={"username": "loginuser", "password": "Login1234!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={"username": "u3", "email": "u3@t.com", "password": "Right1234!"})
    resp = await client.post("/auth/login", json={"username": "u3", "password": "Wrong1234!"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client, auth_headers):
    resp = await client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


# ── Products Tests ────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_product(client, auth_headers):
    resp = await client.post("/products/", headers=auth_headers, json={
        "name": "Test Whiskey", "sku": "TST-001", "category": "Hard Liquor",
        "cost_price": 15.00, "sell_price": 28.99, "stock": 20, "reorder_point": 5
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Whiskey"
    assert data["margin_pct"] > 0


@pytest.mark.asyncio
async def test_list_products(client, auth_headers):
    await client.post("/products/", headers=auth_headers, json={
        "name": "Beer Test", "sku": "BT-001", "category": "Beer",
        "cost_price": 8.00, "sell_price": 14.99, "stock": 30, "reorder_point": 10
    })
    resp = await client.get("/products/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_duplicate_sku(client, auth_headers):
    await client.post("/products/", headers=auth_headers, json={
        "name": "Vodka A", "sku": "VOD-001", "category": "Hard Liquor",
        "cost_price": 10.00, "sell_price": 20.00, "stock": 10, "reorder_point": 5
    })
    resp = await client.post("/products/", headers=auth_headers, json={
        "name": "Vodka B", "sku": "VOD-001", "category": "Hard Liquor",
        "cost_price": 10.00, "sell_price": 20.00, "stock": 10, "reorder_point": 5
    })
    assert resp.status_code == 400


# ── Analytics Tests ───────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_dashboard(client, auth_headers):
    resp = await client.get("/analytics/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_revenue" in data
    assert "total_products" in data
    assert "low_stock_count" in data


@pytest.mark.asyncio
async def test_monthly_analytics(client, auth_headers):
    resp = await client.get("/analytics/monthly", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_seasonal_analytics(client, auth_headers):
    resp = await client.get("/analytics/seasonal", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Health Check ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
