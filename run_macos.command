# Aller dans le dossier du script
cd "$(dirname "$0")"

# Mettre à jour le code depuis GitHub
git pull

# Installer / mettre à jour les dépendances Python
pip install --upgrade -r requirements.txt

# Lancer main.py
python main.py &

# Patienter un instant pour que le serveur se lance
sleep 2

# Ouvrir l’application web dans le navigateur
open http://127.0.0.1:5000