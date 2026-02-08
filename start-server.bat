@echo off
setlocal
REM Try common venv locations: venv and .venv
if exist "%~dp0venv\Scripts\activate.bat" (
  call "%~dp0venv\Scripts\activate.bat"
) else if exist "%~dp0.venv\Scripts\activate.bat" (
  call "%~dp0.venv\Scripts\activate.bat"
) else (
  echo Aucune virtualenv trouvée dans venv ou .venv, execution sans activation.
)
python manage.py runserver
endlocal
