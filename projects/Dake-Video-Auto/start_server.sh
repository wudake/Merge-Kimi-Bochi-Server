#!/bin/bash
cd /home/dake/Dake-Video-Auto
source venv/bin/activate
exec python3 app_simple.py >> logs/app.log 2>&1