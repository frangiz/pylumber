#!/bin/bash

cd "$(dirname "$0")"

git pull
pip install -r requirements.txt
kill $(cat app.pid)
while true; do
    flask db upgrade
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo "Deploy command failed, retrying in 5 secs..."
    sleep 5
done
echo $(git rev-parse --short HEAD) > version.txt
gunicorn -p app.pid --access-logfile logs/gunicorn.log -D -b :5000 pylumber:app
echo "Upgrade done, app started again"