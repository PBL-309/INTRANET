#!/bin/bash
cd /home/sgcpbl/INTRANET
git fetch origin
git reset --hard origin/main
echo "Cambios sincronizados desde GitHub"
pkill -f "gunicorn"
sleep 1
nohup /home/sgcpbl/INTRANET/venv/bin/gunicorn -w 4 -b 0.0.0.0:5001 main:app > /home/sgcpbl/gunicorn.log 2>&1 &
sleep 2
echo "Gunicorn reiniciado con 4 workers"
curl -s http://localhost:5001/ > /dev/null && echo "✓ Servidor disponible en 34.170.131.204:5001"
