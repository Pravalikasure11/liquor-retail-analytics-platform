#!/bin/bash
# Zach's Liquor Store — Local Dev Quick Start
# Run from project root: bash start.sh

echo "🥃 Starting Zach's Liquor Store..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install from python.org"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install from nodejs.org"
    exit 1
fi

# Backend setup
echo ""
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

pip install -r requirements.txt -q
echo "  ✓ Dependencies installed"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ✓ .env created from template"
    echo "  ⚠️  Edit backend/.env and set DATABASE_URL before running"
fi

echo ""
echo "💾 Seeding database..."
python seed.py

echo ""
echo "🚀 Starting backend on http://localhost:8000"
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Frontend setup
cd ../frontend
echo ""
echo "📦 Setting up frontend..."

if [ ! -d "node_modules" ]; then
    npm install -q
    echo "  ✓ npm packages installed"
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

echo "🚀 Starting frontend on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "═══════════════════════════════════════════════"
echo "✅ Zach's Liquor Store is running!"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "   Login: zach / Zach1234! (owner)"
echo "   Login: staff / Staff123! (staff)"
echo "═══════════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop both servers"

wait $BACKEND_PID $FRONTEND_PID
