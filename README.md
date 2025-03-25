# Transforming Lessons into Quizzes

Une application web qui transforme vos documents de cours en quizz interactifs en utilisant l'intelligence artificielle Gemini de Google.

## 📋 Description

Cette application permet aux enseignants et étudiants de :
- Télécharger des documents de cours au format PDF
- Générer automatiquement des quizz basés sur le contenu du document
- Personnaliser le format des questions, le système de notation et le nombre de questions
- Passer les quizz et suivre ses résultats
- Générer plusieurs versions d'un même quizz

## 🛠️ Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- **Python 3.8+** : [Télécharger Python](https://www.python.org/downloads/)
- **pip** (gestionnaire de paquets Python, généralement inclus avec Python)
- **Git** : [Télécharger Git](https://git-scm.com/downloads)
- **Clé API Gemini** : [Obtenir sur Google AI Studio](https://ai.google.dev/)
- **Poppler** (utilisé par pdf2image) :
  - macOS : `brew install poppler` (installation de brew : [instructions](https://brew.sh/))
  - Ubuntu/Debian : `sudo apt-get install poppler-utils`
  - Windows : [Instructions d'installation](https://github.com/oschwartz10612/poppler-windows/releases/)

## 🚀 Installation

1. **Clonez le dépôt** :
   ```bash
   cd Documents
   git clone https://github.com/hpktz/transforming-lessons-into-quizzes.git
   cd transforming-lessons-into-quizzes
   ```

2. **Installez les dépendances** :
   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **Configurez l'API Gemini** :
   
   Créez un fichier `.env` via la ligne de commande** :
    ```bash
    echo "GEMINI_API_KEY=votre_clé_api_gemini_ici" > .env
    ```   

## ▶️ Démarrage de l'application

### Méthode simple (scripts fournis)

Selon votre système d'exploitation, utilisez l'un des scripts suivants en double-cliquant dessus ou en l'exécutant :

- **Windows** : Double-cliquez sur `run_windows.bat`
- **macOS** : 
  ```bash
  chmod +x run_macos.command
  ```
  Puis double-cliquez sur `run_macos.command`
- **Linux** : 
  ```bash
  chmod +x run_linux.sh
  ```
Puis exécutez `./run_linux.sh`

### Méthode manuelle (ligne de commande)

1. **Exportez votre clé API Gemini** :
   ```bash
   # Sur macOS/Linux
   export GEMINI_API_KEY=votre_clé_api_gemini_ici
   
   # Sur Windows (PowerShell)
   $env:GEMINI_API_KEY="votre_clé_api_gemini_ici"
   
   # Sur Windows (CMD)
   set GEMINI_API_KEY=votre_clé_api_gemini_ici
   ```

2. **Lancez l'application Flask** :
   ```bash
   python main.py
   ```

3. **Ouvrez votre navigateur** à l'adresse : http://127.0.0.1:5000

## 📂 Structure du projet

- `/static` : Ressources statiques (CSS, JS, fichiers utilisateur)
- `/templates` : Templates HTML pour le rendu des pages
- `/flask_session` : Stockage des sessions Flask
- `main.py` : Point d'entrée de l'application
- `requirements.txt` : Liste des dépendances Python
- Scripts de lancement : `run_windows.bat`, `run_macos.command`, `run_linux.sh`

## 🔍 Dépannage

### Problèmes avec pdf2image

Si vous rencontrez des erreurs avec pdf2image :
1. Vérifiez que Poppler est correctement installé
2. Assurez-vous que Poppler est dans votre PATH

### Erreurs d'API Gemini

1. Vérifiez que votre clé API est correcte
2. Assurez-vous que votre clé a des crédits disponibles
3. Vérifiez que la variable d'environnement `GEMINI_API_KEY` est correctement définie

## 🎯 Utilisation

1. Cliquez sur "Créer un quizz"
2. Entrez les informations sur le cours et téléchargez un PDF
3. Configurez les paramètres du quizz (type, notation, nombre de questions)
4. Attendez la génération (cela peut prendre quelques instants)
5. Accédez à votre quizz depuis la page d'accueil
6. Lancez le quizz en cliquant sur l'icône de lecture
7. Répondez aux questions et soumettez vos réponses

---
*Ce projet utilise l'API Google Gemini pour l'analyse et la génération de contenu.*
