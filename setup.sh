#!/bin/bash
echo "=== ConvoGreen Setup ==="

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip and installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Starting ConvoGreen on http://0.0.0.0:8766"
uvicorn main:app --host 0.0.0.0 --port 8766 --reload
