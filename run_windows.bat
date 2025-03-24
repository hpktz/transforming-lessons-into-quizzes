@echo off
REM Se placer dans le dossier du script
cd /d "%~dp0"

REM Mettre à jour le code depuis GitHub
git pull

REM Installer / mettre à jour les dépendances Python
pip install --upgrade -r requirements.txt

REM Lancer main.py en arrière-plan
start /B python main.py

REM Patienter quelques secondes pour que le serveur se lance
timeout /T 2 > nul

REM Ouvrir l’application web dans le navigateur par défaut
start http://127.0.0.1:5000