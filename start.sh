#!bin/bash
proj_dir="($CODING_PATH)/epaper-todo-ui"
cd "$proj_dir"

source .venv/bin/activate
source ./env.sh

response=$(curl -s "$API_URL")

python app.py "$response"
