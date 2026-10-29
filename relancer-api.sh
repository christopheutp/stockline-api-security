#!/bin/bash
# Arrête puis redémarre l'API StockLine en arrière-plan sur http://127.0.0.1:8000.
# Le journal de l'API est écrit dans api.log.
cd "$(dirname "$0")" || exit 1
pkill -f "uvicorn app.main:app" 2> /dev/null && sleep 1
# Secret de signature des jetons (exercice 1) : généré une fois, lisible par vous seul.
if [ ! -s .secret-jwt ]; then (umask 077 && openssl rand -hex 32 > .secret-jwt); fi
STOCKLINE_JWT_SECRET=$(cat .secret-jwt) nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > api.log 2>&1 &
for _ in $(seq 1 30); do
  if curl -s -o /dev/null http://127.0.0.1:8000/sante; then
    echo "OK : API démarrée sur http://127.0.0.1:8000"
    exit 0
  fi
  sleep 0.5
done
echo "ERREUR : l'API ne démarre pas. Dernières lignes du journal (api.log) :"
tail -20 api.log
exit 1
