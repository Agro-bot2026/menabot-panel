#!/bin/bash
# MenaBot Panel - Script de inicio
# Uso: bash start.sh

echo "🤖 Iniciando MenaBot Panel..."

# ── BACKEND ──────────────────────────────────────────────────────────────────
echo "📦 Instalando dependencias del backend..."
cd backend
pip install -r requirements.txt --break-system-packages -q
cd ..

# ── BOT ──────────────────────────────────────────────────────────────────────
echo "📦 Instalando dependencias del bot..."
cd bot
npm install --silent
cd ..

# ── PM2 ──────────────────────────────────────────────────────────────────────
echo "🚀 Iniciando servicios con PM2..."

pm2 delete menabot-backend 2>/dev/null
pm2 delete menabot-bot 2>/dev/null

pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" \
  --name menabot-backend \
  --cwd ./backend

pm2 start bot/index.js \
  --name menabot-bot

pm2 save

echo ""
echo "✅ MenaBot Panel iniciado!"
echo ""
echo "🌐 API Backend: http://localhost:8000"
echo "🤖 Bot API:     http://localhost:3001"
echo "📱 Panel web:   Abrí frontend/index.html en el navegador"
echo "   (o servilo con: npx serve frontend -p 8080)"
echo ""
echo "👤 Login por defecto: admin / admin123"
echo "   ⚠️  Cambiá la contraseña desde el panel inmediatamente"
echo ""
pm2 logs --lines 20
