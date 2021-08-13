#!/bin/bash

git pull
kill $(cat app.pid)
while true; do
    flask db upgrade
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo "Deploy command failed, retrying in 5 secs..."
    sleep 5
done
gunicorn -p app.pid -D -b :5000 pylumber:app
echo "Upgrade done, app started again"