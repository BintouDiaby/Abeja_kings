Param()
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venv = Join-Path $root 'venv\Scripts\Activate.ps1'
$dotvenv = Join-Path $root '.venv\Scripts\Activate.ps1'
if (Test-Path $venv) {
  & $venv
} elseif (Test-Path $dotvenv) {
  & $dotvenv
} else {
  Write-Host "Aucune virtualenv trouvée dans 'venv' ou '.venv' ; utilisation de Python du système."
}
python manage.py runserver
