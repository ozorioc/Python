param(
  [int]$Port = 8501
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path ".venv")) {
  Write-Host "[setup] Creating venv .venv" -ForegroundColor Cyan
  py -3 -m venv .venv
}

$python = Join-Path ".venv" "Scripts/python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}

Write-Host "[setup] Upgrading pip/setuptools/wheel" -ForegroundColor Cyan
& $python -m pip install --upgrade pip setuptools wheel

Write-Host "[setup] Installing requirements" -ForegroundColor Cyan
& $python -m pip install -r requirements.txt

Write-Host "[run] Starting Streamlit on port $Port" -ForegroundColor Green
& $python -m streamlit run streamlit_app.py --server.port $Port


