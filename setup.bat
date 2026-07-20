@echo off
echo === ConvoGreen Setup ===

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo Upgrading pip and installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Starting ConvoGreen on http://0.0.0.0:8766
uvicorn main:app --host 0.0.0.0 --port 8766 --reload
