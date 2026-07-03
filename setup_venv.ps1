# Erstellt das venv
python -m venv venv
# Aktiviert es (benötigt ggf. Set-ExecutionPolicy, siehe unten)
.\venv\Scripts\Activate.ps1
# Updates und Pakete
python -m pip install --upgrade pip
pip install ipykernel jupyter
Write-Host "ERFOLG: venv ist bereit und Pakete sind installiert" -ForegroundColor Green
