#!/bin/bash

# Will not work if the terminal is closed. Need to find another way to start the application again.

git pull
curl http://localhost:5000/api/shutdown
flask run &
echo "Upgrade done"