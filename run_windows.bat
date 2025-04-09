@echo off
REM filepath: /Users/hippolyte/Documents/transforming-lessons-into-quizzes/run_windows.bat

REM Aller dans le dossier du script
cd /d "%~dp0"

REM Mettre à jour le code depuis GitHub
git pull

REM Installer / mettre à jour les dépendances Python
python -m pip install --upgrade -r requirements.txt

REM Préparer l'ouverture du navigateur après un délai
start "" cmd /c "timeout /t 2 /nobreak && start http://127.0.0.1:5000"

REM Lancer main.py avec Flask et werkzeug (sans détacher le processus)
set FLASK_APP=main.py
set FLASK_ENV=development
python -m flask run --debug