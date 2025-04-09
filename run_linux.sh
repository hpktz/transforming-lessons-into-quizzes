#!/bin/bash
# filepath: /Users/hippolyte/Documents/transforming-lessons-into-quizzes/run_linux.sh

# Aller dans le dossier du script
cd "$(dirname "$0")"

# Mettre à jour le code depuis GitHub
git pull

# Installer / mettre à jour les dépendances Python
python3 -m pip install --upgrade -r requirements.txt

# Lancer main.py avec Flask et werkzeug (sans détacher le processus)
# Ouvrir le navigateur après un court délai
(sleep 2 && xdg-open http://127.0.0.1:5000) &
FLASK_APP=main.py FLASK_ENV=development python3 -m flask run --debug