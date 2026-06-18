#!/bin/bash

# ─────────────────────────────────────────
#  MenaBot Panel - Instalador automático
# ─────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "  __  __                 ____        _   "
echo " |  \/  | ___ _ __  __ _| __ )  ___ | |_ "
echo " | |\/| |/ _ \ '_ \/ _\` |  _ \ / _ \| __|"
echo " | |  | |  __/ | | | (_| | |_) | (_) | |_ "
echo " |_|  |_|\___|_| |_|\__,_|____/ \___/ \__|"
echo -e "${NC}"
echo -e "${YELLOW}  Panel de Notificaciones WhatsApp${NC}"
echo "  ======================================"
echo ""

# Obtener IP
IP=$(curl -s https://api.ipify.org)
echo -e "${GREEN}► IP del servidor: $IP${NC}"
echo ""

# 1. Actualizar sistema
echo -e "${YELLOW}[1/6] Actualizando sistema...${NC}"
apt update -qq && apt upgrade -y -qq

# 2. Instalar dependencias del sistema
echo -e "${YELLOW}[2/6] Instalando Python, Node.js, nginx...${NC}"
apt install -y -qq python3 python3-pip git nginx
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - > /dev/null 2>&1
apt install -y -qq nodejs
npm install -g pm2 > /dev/null 2>&1

# 3. Clonar repositorio
echo -e "${YELLOW}[3/6] Descargando MenaBot Panel...${NC}"
rm -rf /var/www/menabot-panel
git clone https://github.com/Agro-bot2026/menabot-panel /var/www/menabot-panel -q
cd /var/www/menabot-panel

# 4. Instalar dependencias
echo -e "${YELLOW}[4/6] Instalando dependencias...${NC}"
pip install fastapi uvicorn sqlalchemy "passlib[bcrypt]" "python-jose[cryptography]" python-multipart aiofiles httpx "bcrypt==4.0.1" --break-system-packages -q
cd bot && npm install --silent && cd ..

# 5. Configurar nginx
echo -e "${YELLOW}[5/6] Configurando nginx...${NC}"
cat > /etc/nginx/sites-available/menabot << NGINX
server {
    listen 80;
    server_name _;

    root /var/www/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Authorization, Content-Type";
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
    }

    location /bot/ {
        proxy_pass http://127.0.0.1:3001/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Authorization, Content-Type";
    }
}
NGINX

ln -sf /etc/nginx/sites-available/menabot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t -q && systemctl restart nginx

# Copiar frontend
cp /var/www/menabot-panel/frontend/index.html /var/www/html/index.html

# Reemplazar IP en el panel
sed -i "s|const API = '/api'|const API = '/api'|" /var/www/html/index.html

# 6. Iniciar servicios con PM2
echo -e "${YELLOW}[6/6] Iniciando servicios...${NC}"
pm2 delete all > /dev/null 2>&1

pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" \
  --name menabot-backend \
  --cwd /var/www/menabot-panel/backend > /dev/null 2>&1

pm2 start /var/www/menabot-panel/bot/index.js \
  --name menabot-bot > /dev/null 2>&1

pm2 save > /dev/null 2>&1
pm2 startup > /dev/null 2>&1
systemctl enable pm2-root > /dev/null 2>&1

# Esperar que arranque
sleep 4

# Verificar
STATUS=$(pm2 jlist 2>/dev/null | python3 -c "
import sys,json
p=json.load(sys.stdin)
for x in p: print(x['name'],x['pm2_env']['status'])
" 2>/dev/null)

echo ""
echo -e "${GREEN}══════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ MenaBot Panel instalado con éxito${NC}"
echo -e "${GREEN}══════════════════════════════════════${NC}"
echo ""
echo -e "  🌐 Panel web:  ${YELLOW}http://$IP${NC}"
echo -e "  👤 Usuario:    ${YELLOW}admin${NC}"
echo -e "  🔑 Contraseña: ${YELLOW}admin123${NC}"
echo ""
echo -e "  ${RED}⚠️  Cambiá la contraseña desde Perfil al ingresar${NC}"
echo ""
