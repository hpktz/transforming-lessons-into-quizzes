from flask import Flask, request, jsonify, render_template, session, url_for, redirect, flash, make_response
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from urllib.parse import quote

import os
import random
import logging
from logging.handlers import TimedRotatingFileHandler
import json
import emoji
import subprocess

from difflib import get_close_matches

from google import genai
from google.genai import types

from pdf2image import convert_from_path

import shutil
from datetime import datetime, timedelta
import pytz

LOG_FILE = "app.log"

# Création d'un handler avec rotation toutes les 24h, et conservation pendant 2 jours
handler = TimedRotatingFileHandler(
    LOG_FILE, when="D", interval=1, backupCount=2, encoding='utf-8'
)

# Définir le format du log
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

# Configuration du logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)  

def get_paris_time():
    """Retourne l'heure actuelle au fuseau horaire de Paris."""
    paris_tz = pytz.timezone('Europe/Paris')
    return datetime.now(pytz.UTC).astimezone(paris_tz)

def parse_datetime_with_tz(datetime_str, format_str='%Y-%m-%d %H:%M:%S'):
    """Convertit une chaîne de date en datetime avec le fuseau horaire de Paris."""
    naive_datetime = datetime.strptime(datetime_str, format_str)
    paris_tz = pytz.timezone('Europe/Paris')
    return paris_tz.localize(naive_datetime)

app = Flask(__name__)

secret_key = os.urandom(24)
app.secret_key = secret_key

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
# Override the default static file handler to add authentication
app.static_folder = 'static'
app.static_url_path = '/static'

original_send_static_file = app.send_static_file

def custom_send_static_file(filename):
    protected_paths = ['user_files', 'user_data.json']
    
    is_protected = any(filename.startswith(path) for path in protected_paths)
    
    if is_protected and not current_user.is_authenticated:
        return redirect(url_for('login_page', next=request.url))
    
    return original_send_static_file(filename)

app.send_static_file = custom_send_static_file
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    password = request.form['password']
    password_to_check = os.environ['PASSWORD']
    
    if password == password_to_check:
        user = User(1)
        login_user(user)
    else:            
        flash("Mot de passe incorrect", "error")
        return redirect(url_for('login_page'))
    
    next_page = request.args.get('next')
    return redirect(next_page or url_for('index'))

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/', methods=['GET'])
@login_required
def index():
    try:
        # Check if the folder.json file exists
        if not os.path.exists(os.path.join(app.root_path, 'static', 'folder.json')):
            if os.path.exists(os.path.join(app.root_path, 'static', 'user_data.json')):
                user_data = json.load(open(os.path.join(app.root_path, 'static', 'user_data.json')))
                quizzes = [key for key in user_data.keys()]
            else:
                quizzes = []

            folder_data = {
                'id': random.randint(1000000000000000, 9999999999999999),
                'name': 'Home',
                'color': '#333333',
                'folders': [],
                'quizzes': quizzes
            }
            with open(os.path.join(app.root_path, 'static', 'folder.json'), 'w') as folder_file:
                json.dump(folder_data, folder_file, indent=4) 
        else:
            with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
                folder_data = json.load(folder_file)   
    
        return redirect(url_for('folder', folder_id=folder_data['id']))
    except Exception as e:
        logging.error(e)
        flash("Une erreur est survenue lors de la récupération des données", "error")
        return render_template('home.html', data=[], folder_data={}, current_folder={}, path=[], path_info=[], id_folder=0)
    
@app.route('/folder/<int:folder_id>', methods=['GET'])
@login_required
def folder(folder_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
            
        if 'quizz' in request.args: 
            query = int(request.args.get('quizz'))
        else:
            query = 0
        
        def find_folder(folders, folder_id):
            for folder in folders:
                if folder['id'] == folder_id:
                    return folder
                else:
                    found_folder = find_folder(folder['folders'], folder_id)
                    if found_folder:
                        return found_folder
            return None
        
        current_folder = find_folder([folder_data], folder_id)
        
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        data_to_show = []
        for key in current_folder['quizzes']:
            last_attempt = "~"
        
            if data[str(key)]['quizzes'] and len(data[str(key)]['quizzes']) > 0:
                last_version = data[str(key)]['quizzes'][-1]
                if 'attempts' in last_version and len(last_version['attempts']) > 0:
                    last_attempt = last_version['attempts'][-1]['score']
            data_to_show.append({
                'id': key,
                'title': data[str(key)]['title'],
                'color': data[str(key)]['color'],
                'emoji': data[str(key)]['emoji'],
                'size': data[str(key)]['size'],
                'preview_path': url_for('static', filename=f'pdf_preview/preview_{key}.jpg'),
                'last_attempt': last_attempt,
                'quizz_amount': len(data[str(key)]['quizzes']),
                                'to_highlight': True if int(key) == query else False
            })
            
        # Get all the id of the folders from the root folder to this folder (the path)
        path = []
        def get_path(folders, folder_id):
            for folder in folders:
                if folder['id'] == folder_id:
                    path.append(folder['id'])
                    return True
                else:
                    if get_path(folder['folders'], folder_id):
                        path.append(folder['id'])
                        return True
            return False
        get_path([folder_data], folder_id)
        
        path_info = []
        path_info.append({
            'id': folder_data['id'],
            'name': folder_data['name'],
            'color': folder_data['color']
        })
        path.reverse()
        folder_path_current = folder_data
        for folder_id in path:
            for folders in folder_path_current['folders']:
                if folders['id'] == folder_id:
                    path_info.append({
                        'id': folder_id,
                        'name': folders['name'],
                        'color': folders['color']
                    })
                    folder_path_current = folders
                    break
                        
        return render_template('home.html', 
                               data=data_to_show, 
                               folder_data=folder_data, 
                               current_folder=current_folder, 
                               path=path, 
                               path_info=path_info,
                               id_folder=folder_id)
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))
    
@app.route('/create_folder/<int:current_folder_id>', methods=['POST'])
@login_required
def create_folder(current_folder_id):
    try:
        folder_name = request.form['folder_name']
        folder_color = request.form['folder_color']
        
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
        
        new_folder = {
            'id': random.randint(1000000000000000, 9999999999999999),
            'name': folder_name,
            'color': folder_color,
            'folders': [],
            'quizzes': []
        }
        
        if current_folder_id == 0:
            folder_data['folders'].append(new_folder)
        else:
            def add_folder_to_parent(folders):
                for folder in folders:
                    if folder['id'] == current_folder_id:
                        folder['folders'].append(new_folder)
                        break
                    else:
                        add_folder_to_parent(folder['folders'])
            
            add_folder_to_parent([folder_data])
        
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'w') as folder_file:
            json.dump(folder_data, folder_file, indent=4)
        
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))
    
@app.route('/move_quizz/<int:quizz_id>/<int:folder_to_move_id>', methods=['POST'])
@login_required
def move_folder(quizz_id, folder_to_move_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
        
        def remove_quizz_from_folder(folders):
            for folder in folders:
                if quizz_id in folder['quizzes']:
                    folder['quizzes'].remove(quizz_id)
                    break
                else:
                    remove_quizz_from_folder(folder['folders'])
        
        def move_quizz_to_folder(folders):
            for folder in folders:
                if folder['id'] == folder_to_move_id:
                    folder['quizzes'].append(quizz_id)
                    break
                else:
                    move_quizz_to_folder(folder['folders'])
        
        remove_quizz_from_folder([folder_data])
        move_quizz_to_folder([folder_data])
        
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'w') as folder_file:
            json.dump(folder_data, folder_file, indent=4)
        
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))
    
@app.route('/delete/<int:quizz_id>', methods=['GET'])
@login_required
def delete(quizz_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        del data[str(quizz_id)]
        
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as file:
            json.dump(data, file, indent=4)
            
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
        
        def remove_quizz_from_folder(folders):
            for folder in folders:
                if quizz_id in folder['quizzes']:
                    folder['quizzes'].remove(quizz_id)
                    return folder['id']
            else:
                folder_id = remove_quizz_from_folder(folder['folders'])
                if folder_id:
                    return folder_id
                return None
        
        folder_id = remove_quizz_from_folder([folder_data])
        
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'w') as folder_file:
            json.dump(folder_data, folder_file, indent=4)
        
        # Delete the preview image and the PDF file
        preview_path = os.path.join(app.root_path, 'static', 'pdf_preview', f'preview_{quizz_id}.jpg')
        pdf_path = os.path.join(app.root_path, 'static', 'user_files', f'file_quizz_{quizz_id}.pdf')
        if os.path.exists(preview_path):
            os.remove(preview_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
        # Save the entire JSON data in cookies with 1 year expiration
        response = make_response(redirect(url_for('folder', folder_id=folder_id)))
        response.set_cookie('user_data', json.dumps(data), max_age=31536000)
        return response
        
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))
    
@app.route('/get_quizz/<int:quizz_id>', methods=['GET'])
@login_required
def get_quizz(quizz_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        quizz = data[str(quizz_id)]
        
        data_to_show = {
            'id': quizz_id,
            'title': quizz['title'],
            'color': quizz['color'],
            'emoji': quizz['emoji'],
            'size': quizz['size'],
            'preview_path': url_for('static', filename=f'pdf_preview/preview_{quizz_id}.jpg'),
            'pdf_path': url_for('static', filename=f'user_files/file_quizz_{quizz_id}.pdf'),
            'quizz_amount': len(quizz['quizzes']),
            'quizzes': quizz['quizzes']
        }
        
        return jsonify(data_to_show)
    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Quizz not found'}), 404
    
@app.route('/modify/<int:quizz_id>', methods=['POST'])
@login_required
def modify_quizz(quizz_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        quizz = data[str(quizz_id)]
        
        # Get the new values from the form
        new_title = request.form['quizz_name']
        new_color = request.form['quizz_color']
        new_emoji = request.form['quizz_emoji']
        
        # Update the quizz data
        quizz['title'] = new_title
        quizz['color'] = new_color
        quizz['emoji'] = new_emoji
        
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
        
        def find_folder(folders, quizz_id):
            for folder in folders:
                if quizz_id in folder['quizzes']:
                    return folder['id']
                else:
                    found_folder = find_folder(folder['folders'], quizz_id)
                    if found_folder:
                        return found_folder
            return None
        folder_id = find_folder([folder_data], quizz_id)
        
        # Check if the quizz emoji is valid
        if not emoji.is_emoji(new_emoji):
            flash("L'emoji fourni n'est pas valide", "error")
            return redirect(url_for('folder', folder_id=folder_id))
        
        # Save the updated data back to the JSON file
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as file:
            json.dump(data, file, indent=4)
        
        # Redirect to the right folder
        return redirect(url_for('folder', folder_id=folder_id))
    except Exception as e:
        logging.error(e)
    
        flash("Une erreur est survenue lors de la modification du quiz", "error")
        return redirect(url_for('index'))
    
@app.route('/delete_folder/<int:folder_id>', methods=['POST'])
@login_required
def delete_folder(folder_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
        
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as user_data_file:
            user_data = json.load(user_data_file)
        
        def remove_folder_and_quizzes(folders):
            for folder in folders:
                if folder['id'] == folder_id:
                    def delete_quizzes_recursively(subfolder):
                        for subfolder_item in subfolder['folders']:
                            delete_quizzes_recursively(subfolder_item)
                        for quizz_id in subfolder['quizzes']:
                            if str(quizz_id) in user_data:
                                # Delete the preview image and PDF file
                                preview_path = os.path.join(app.root_path, 'static', 'pdf_preview', f'preview_{quizz_id}.jpg')
                                pdf_path = os.path.join(app.root_path, 'static', 'user_files', f'file_quizz_{quizz_id}.pdf')
                                if os.path.exists(preview_path):
                                    os.remove(preview_path)
                                if os.path.exists(pdf_path):
                                    os.remove(pdf_path)
                                del user_data[str(quizz_id)]
                    
                    delete_quizzes_recursively(folder)
                    folders.remove(folder)
                    return True
                else:
                    if remove_folder_and_quizzes(folder['folders']):
                        return True
            return False
        
        remove_folder_and_quizzes([folder_data])
        
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'w') as folder_file:
            json.dump(folder_data, folder_file, indent=4)
        
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as user_data_file:
            json.dump(user_data, user_data_file, indent=4)
        
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))
    
@app.route('/get_folder/<int:folder_id>', methods=['GET'])
@login_required
def get_folder(folder_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
        
        def find_folder(folders, folder_id):
            for folder in folders:
                if folder['id'] == folder_id:
                    return folder
                else:
                    found_folder = find_folder(folder['folders'], folder_id)
                    if found_folder:
                        return found_folder
            return None
        
        current_folder = find_folder([folder_data], folder_id)
        
        return jsonify(current_folder)
    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Folder not found'}), 404
    
@app.route('/modify_folder/<int:folder_id>', methods=['POST'])
@login_required
def modify_folder(folder_id):
    try:
        folder_name = request.form['folder_name']
        folder_color = request.form['folder_modify_color']
        
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
        
        def find_and_modify_folder(folders):
            for folder in folders:
                if folder['id'] == folder_id:
                    folder['name'] = folder_name
                    folder['color'] = folder_color
                    return True
                else:
                    if find_and_modify_folder(folder['folders']):
                        return True
            return False
        
        find_and_modify_folder([folder_data])
        
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'w') as folder_file:
            json.dump(folder_data, folder_file, indent=4)
        
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))


@app.route('/create/1/<int:folder_id>', methods=['GET'])
@login_required
def create1(folder_id):
    session['folder_id'] = folder_id
    return render_template('creation-step1.html')

@app.route('/create/2', methods=['POST'])
@login_required
def create2():
    try:
        data = request.form
        
        file = request.files['course_pdf']
        temp_file_path = os.path.join('/tmp', file.filename)
        file.save(temp_file_path)

        session['course_name'] = data['course_name']
        session['course_level'] = data['course_level']
        session['course_pdf'] = temp_file_path
        
        return render_template('creation-step2.html')
    except Exception as e:
        logging.error(e)
        return render_template('creation-step1.html', error_mess="Une erreur est survenue")

@app.route('/create/3', methods=['POST'])
@login_required
def create3():
    try:
        data = request.form

        session['quizz_type'] = data['quizz_type']
        session['quizz_notation'] = data['quizz_notation']
        session['quizz_size'] = data['quizz_size']
        session['quizz_notions'] = data['notions']

        quizz_id = random.randint(1000000000000000, 9999999999999999)

        # Load the json file
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            quizz = json.load(file)     
        
        client =genai.Client(api_key=os.environ['GEMINI_API_KEY'])
        
        files = [
            client.files.upload(file=session['course_pdf'])
        ]
        
        model = "gemini-2.5-flash-preview-04-17"
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=files[0].uri,
                        mime_type=files[0].mime_type,
                    ),
                    types.Part.from_text(text=f"""
                    **Objectif Principal :** Générer un quiz de **{session['quizz_size']} questions** évaluant la compréhension **approfondie** et la **capacité d'application/raisonnement** basées **UNIQUEMENT et EXCLUSIVEMENT** sur le contenu du document PDF fourni. Agis comme un expert du domaine dont la **SEULE** source de vérité est ce document.

                    **Règle Fondamentale :** **AUCUNE connaissance extérieure** ne doit être utilisée, ni pour formuler les questions, ni pour déterminer les bonnes réponses ou les distracteurs. Le PDF est la référence absolue et unique.

                    **Instructions Détaillées :**

                    1.  **Couverture du Document :** Assure-toi que les questions couvrent **l'intégralité du document** (du début à la fin), reflétant une compréhension globale et pas seulement des premières sections. Ne te limite pas aux titres ou aux introductions de section.

                    2.  **Format et Structure du Quiz :**
                        * Le quiz doit être au format **{session['quizz_type']}**.
                        * **Choix Multiple (si applicable) :**
                            * **TOUTES** les questions à choix multiples DOIVENT comporter **PLUSIEURS réponses correctes**.
                            * Propose un total de **4 à 6 options** par question (incluant bonnes réponses et distracteurs pertinents).
                        * **Mixte (si applicable) :** Inclut un **mélange équilibré** de questions à réponse unique et de questions à réponses multiples (respectant la règle ci-dessus).
                        * **Questions Spécifiant un Nombre :** Même si une question demande "Quels sont les 2 avantages...", propose **TOUJOURS plus d'options** (ex: 4 ou 5 au total), forçant l'identification des bonnes réponses parmi un ensemble plus large de distracteurs plausibles issus du PDF.
                        * **Identification des Bonnes Réponses :** Indique les bonnes réponses en reprenant **TEXTUELLEMENT** leur contenu exact (leurs valeurs). **JAMAIS** de lettres ou de positions (ex : "Les bonnes réponses sont : 'Concept A tel que décrit', 'Méthode B expliquée page X'.").
                        * **Présentation :** Ne numérote **NI** les questions, **NI** les options. Présente-les simplement séquentiellement.
                        * **Ordre :** L'ordre des questions doit être **aléatoire** et ne **PAS** suivre l'ordre du document.

                    3.  **Contenu et Style des Questions :**
                        * **INSTRUCTION CRITIQUE - Formulation Directe :** NE JAMAIS utiliser de tournures comme "Selon le document...", "D'après le PDF...". Pose les questions **directement**, comme à un étudiant qui **maîtrise le contenu du PDF**. Le PDF est la référence factuelle **implicite**. (Ex: Au lieu de "Selon le PDF, comment définir X ?", demande "Comment X est-il défini ?" ou "Quelles caractéristiques définissent X ?").
                        * **Système de Notation :** Applique le système suivant : **{session['quizz_notation']}**.
                        * **Notions Obligatoires :** Intègre **impérativement** des questions (idéalement d'application/raisonnement) sur : **{session['quizz_notions']}**.
                        * **VARIÉTÉ et PROFONDEUR (Instruction Clé) :**
                            * **Mix de Styles :** Va au-delà du simple rappel. Inclus des questions demandant :
                                * **Identification/Classification :** Reconnaître des concepts, types, catégories décrits.
                                * **Comparaison/Contraste :** Analyser les similarités/différences entre méthodes/théories du PDF.
                                * **Analyse de Cause/Effet :** Identifier les liens de causalité expliqués dans le PDF.
                                * **Application de Procédure/Méthode :** Suivre les étapes d'un processus décrit dans le PDF.
                                * **Calcul/Interprétation :** Utiliser une formule ou interpréter des données/graphiques présentés dans le PDF.
                            * **FOCUS MAJEUR - Application & Raisonnement (Vise 20-35% du quiz) :** Ces questions doivent exiger **plus qu'une simple récupération d'information**. Elles doivent tester la capacité à **utiliser activement, combiner, et inférer** à partir des connaissances du PDF.
                                * **Crée des Mini-Scénarios ou Problèmes :** Propose des situations **concrètes et plausibles**, des **études de cas très simplifiées**, ou des **ensembles de données**, TOUJOURS **strictement inspirés ou conformes** aux exemples, contextes ou types de données présents dans le PDF.
                                * **Formulation des Questions d'Application :**
                                    * "Face à [Scénario basé sur le PDF], quelle serait l'approche prioritaire en utilisant les principes de [Concept du PDF] ?"
                                    * "Analysez ces [Type de données comme dans le PDF] : quelle(s) conclusion(s) spécifique(s) peut-on tirer concernant [Phénomène décrit dans le PDF], en se basant **uniquement** sur les éléments fournis dans le document ?"
                                    * "Étant donné [Paramètres spécifiques issus du PDF], quel serait le résultat de l'application de la méthode [Nom méthode du PDF] ?"
                                    * "Quel(s) outil(s) ou critère(s) **décrit(s) dans ce document** serai(en)t le(s) plus pertinent(s) pour évaluer/résoudre [Problème spécifique formulé avec les termes du PDF] ? Pourquoi (selon le PDF) ?"
                                    * "Si l'on modifie le paramètre X comme suit [Variation plausible selon le PDF], quel impact cela aurait-il sur Y, d'après les mécanismes expliqués dans le document ?"
                                * **Exigence Clé :** La question doit obliger à **mobiliser et appliquer** une ou plusieurs informations/méthodes du PDF pour trouver la réponse, pas seulement à la localiser. Pense "Que ferait quelqu'un qui a *compris et intégré* ce passage du PDF face à cette situation ?".

                    4.  **Qualité des Options et Distracteurs :**
                        * **Toutes** les options (correctes et incorrectes) doivent être **plausibles** dans le contexte du PDF.
                        * Les distracteurs doivent être **pertinents** mais **clairement faux ou non supportés par le contenu spécifique du PDF**. Ils peuvent représenter des erreurs communes *discutées ou implicitement contredites* dans le document, ou des concepts proches mais distincts.
                        * Équilibre la longueur et le style des options.

                    5.  **Positionnement Aléatoire des Réponses :** Pour chaque question, la ou les bonnes réponses doivent être positionnées **aléatoirement** parmi les options. Évite toute tendance systématique.

                    6.  **Sourçage et Justification Rigoureux (Pour CHAQUE question) :**
                        * **Page(s) Exacte(s) :** Indique le numéro de page précis dans le PDF.
                        * **Concept(s) Clé(s) / Passage(s) Pertinent(s) :** Référence le texte, l'image, le tableau, la formule qui **justifie SANS AMBIGUÏTÉ la question ET la ou les bonnes réponses**.
                        * **Justification d'Application :** Pour les questions d'application/raisonnement, la référence doit pointer vers le(s) principe(s), méthode(s) ou information(s) du PDF qui sont **directement mobilisés ou combinés** pour répondre correctement au scénario/problème posé. La justification doit expliquer *comment* le PDF mène à la bonne réponse et invalide les distracteurs.

                    *(Meta-instruction interne pour l'IA : Lors de la création des questions d'application, décompose le raisonnement : 1. Identifier le concept/méthode clé du PDF à tester. 2. Créer un scénario/problème qui nécessite l'application de ce concept/méthode, en utilisant uniquement des éléments/contextes présents ou implicites dans le PDF. 3. Déterminer la ou les réponses correctes en appliquant strictement le PDF. 4. Créer des distracteurs plausibles mais réfutables par le PDF.)*
                    """),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.95,
            top_k=40,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            max_output_tokens=65536,
            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type = genai.types.Type.OBJECT,
                required = ["emoji", "title", "questions"],
                properties = {
                    "emoji": genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "Emoji pertinent représentant le sujet principal du quiz.",
                    ),
                    "title": genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "Titre concis et informatif pour le quiz, basé sur le sujet du PDF.",
                    ),
                    "questions": genai.types.Schema(
                        type = genai.types.Type.ARRAY,
                        description = "Liste des questions composant le quiz.",
                        items = genai.types.Schema(
                            type = genai.types.Type.OBJECT,
                            required = ["question", "answers", "correct", "explanation", "sources", "type_question"],
                            properties = {
                                "question": genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                    description = "Texte de la question, formulé directement (SANS 'Selon le document...'), évaluant la compréhension ou l'application du contenu du PDF.",
                                ),
                                "type_question": genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                    description = "Type de question: 'connaissance' ou 'application'",
                                    enum = ["connaissance", "application"]
                                ),
                                "answers": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste des réponses possibles (options). Doit inclure les réponses correctes et des distracteurs plausibles mais incorrects selon le PDF. Viser 4-6 options au total.",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                ),
                                "correct": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste contenant UNIQUEMENT le texte exact (valeur textuelle) de la ou des réponses correctes, telles qu'elles apparaissent dans la liste 'answers'.",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                ),
                                "explanation": genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                    description = "Explication concise justifiant pourquoi la/les réponse(s) sont correctes, en se référant explicitement aux concepts ou informations du PDF.",
                                ),
                                "sources": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste des références précises dans le PDF justifiant la question et la/les réponses correctes.",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.OBJECT,
                                        required = ["source", "page"],
                                        properties = {
                                            "source": genai.types.Schema(
                                                type = genai.types.Type.STRING,
                                                description = "Concept clé, section, ou élément spécifique du PDF (ex: 'Définition du Modèle X', 'Tableau 3.1', 'Méthode de calcul Y') justifiant la réponse.",
                                            ),
                                            "page": genai.types.Schema(
                                                type = genai.types.Type.INTEGER,
                                                description = "Numéro de page exact dans le PDF où trouver la justification.",
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    ),
                },
            ),
            system_instruction=[
                types.Part.from_text(text=f"""**Contexte Impératif :** Positionne-toi comme un(e) enseignant(e) spécialiste rigoureux de {session['course_name']}, 
                    créant une évaluation pour des étudiants de niveau {session['course_level']}. Ton objectif UNIQUE est de créer un quiz qui évalue **précisément et 
                    exclusivement** la compréhension et la capacité d'application du contenu du PDF fourni. Tu ne dois utiliser **AUCUNE autre information ou connaissance**. 
                    La **fidélité absolue** au document source et la **pertinence pédagogique** des questions et des distracteurs (basés uniquement sur le PDF) sont tes priorités 
                    absolues. Le quiz doit servir d'outil fiable de validation et de renforcement, reflétant uniquement le matériel de cours présenté.
                    **OBLIGATION FORMELLE:** Au moins 20% (MAX 35%) des questions générées DOIVENT être des questions d'application/raisonnement 
                    avec des mini-scénarios concrets. Tu dois alterner systématiquement entre questions de connaissance et questions d'application.
                    N'inclus surtout pas dans tes questions avec "Selon le PDF..." ou "D'après le document...".
                """),
            ],
        )

        output = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            output += chunk.text
            
        output = json.loads(output)
        logging.debug(f"API Response: {output}")
        
        pastel_colors = [
            "#FFFBF2",  # Blanc cassé pastel
            "#FFF5E1",  # Pêche très clair
            "#FAF3DD",  # Jaune pastel très clair
            "#F3E8EE",  # Rose pastel pâle
            "#E8F8F5",  # Vert d'eau pastel
            "#E3F2FD",  # Bleu ciel pastel
            "#F8E8FF",  # Lavande très clair
            "#FDF8F5",  # Beige rosé clair
            "#F0F8FF",  # Bleu Alice très pâle
            "#FCF5E5"   # Sable pastel clair
        ]
        
        # Verify if 'correct' answers are in 'answers', and handle mismatches
        for question in output['questions']:
            valid_correct_answers = []
            for correct in question['correct']:
                if correct in question['answers']:
                    valid_correct_answers.append(correct)
                else:
                    # Check for close matches in 'answers'
                    close_matches = get_close_matches(correct, question['answers'], n=1, cutoff=0.9)
                    if close_matches:
                        valid_correct_answers.append(close_matches[0])
            question['correct'] = valid_correct_answers

        quizz[quizz_id] = {
            'title': output['title'],
            'name': session['course_name'],
            'emoji': output['emoji'],
            'level': session['course_level'],
            'type': session['quizz_type'],
            'notation': session['quizz_notation'],
            'notions': session['quizz_notions'],
            'size': session['quizz_size'],
            'color': random.choice(pastel_colors),
            'quizzes': [
                {
                    'id': random.randint(1000000000000000, 9999999999999999),
                    'date': get_paris_time().strftime('%Y-%m-%d'),
                    'questions': output['questions'],
                    'attempts': []
                }
            ]
        }
        
        user_files_dir = os.path.join(app.root_path, 'static', 'user_files')
        os.makedirs(user_files_dir, exist_ok=True)
        user_file_path = os.path.join(user_files_dir, f'file_quizz_{quizz_id}.pdf')
        shutil.copy2(session['course_pdf'], user_file_path)
        os.remove(session['course_pdf'])
        
        pdf_previw_dir = os.path.join(app.root_path, 'static', 'pdf_preview')
        os.makedirs(pdf_previw_dir, exist_ok=True)
        pdf_preview_path = os.path.join(pdf_previw_dir, f'preview_{quizz_id}.jpg')
        images = convert_from_path(user_file_path)
        images[0].save(pdf_preview_path, 'JPEG')

        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as file:
            json.dump(quizz, file, indent=4)
            
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)

        def add_quizz_to_folder(folders, folder_id):
            for folder in folders:
                if folder['id'] == folder_id:
                    folder['quizzes'].append(quizz_id)
                    return True
                if add_quizz_to_folder(folder['folders'], folder_id):
                    return True
            return False

        add_quizz_to_folder([folder_data], session['folder_id'])

        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'w') as folder_file:
            json.dump(folder_data, folder_file, indent=4)
            
        del session['course_name']
        del session['course_level']
        del session['course_pdf']
        del session['quizz_type']
        del session['quizz_notation']
        del session['quizz_size']
        del session['quizz_notions']
        
        folder_id = session['folder_id']
        del session['folder_id']
        
        response = make_response(jsonify({'success': True, 'quizz_id': quizz_id, 'folder_id': folder_id}))
        response.set_cookie('user_data', json.dumps(quizz), max_age=31536000)
        return response
    except Exception as e:
        logging.error(e)
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/extract/1/<int:folder_id>', methods=['GET'])
@login_required
def extract1(folder_id):
    session['folder_id'] = folder_id
    return render_template('extraction-step1.html')

@app.route('/extract/2', methods=['POST'])
@login_required
def extract2():
    try:
        data = request.form
        
        quizz_notation = data['quizz_notation']
        
        course_pdf = request.files['course_pdf']
        quizz_pdf = request.files['quizz_pdf']
        
        course_temp_path = os.path.join('/tmp', course_pdf.filename)
        quizz_temp_path = os.path.join('/tmp', quizz_pdf.filename)
        
        course_pdf.save(course_temp_path)
        quizz_pdf.save(quizz_temp_path)
        
        quizz_id = random.randint(1000000000000000, 9999999999999999)
        
        # Load the json file
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            quizz_data = json.load(file)     
        
        client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
        
        files = [
            client.files.upload(file=course_temp_path),
            client.files.upload(file=quizz_temp_path)
        ]
        
        model = "gemini-2.5-flash-preview-04-17"
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=files[0].uri,
                        mime_type="application/pdf",
                    ),
                    types.Part.from_uri(
                        file_uri=files[1].uri,
                        mime_type="application/pdf",
                    ),
                    types.Part.from_text(text="""
                    **Instructions Détaillées :**

                    **Contexte :** Tu vas traiter deux documents PDF fournis simultanément.
                        1.  **PDF 1 (Cours) :** C'est le support de cours officiel. Il constitue la **source de vérité UNIQUE et EXCLUSIVE** pour toute information, définition, et justification.
                        2.  **PDF 2 (Quiz Existant) :** C'est un quiz pré-existant contenant des questions et des propositions de réponses. Ton rôle est d'extraire son contenu, de le vérifier par rapport au PDF 1, et de le structurer.

                    **Tâches à réaliser IMPÉRATIVEMENT :**

                    1.  **Analyse Initiale du Cours (PDF 1) :**
                        * Détermine un **titre pertinent** résumant le sujet principal du PDF 1.
                        * Propose un **emoji** représentant ce sujet.

                    2.  **Extraction Exhaustive du Quiz Existant (PDF 2) :**
                        * **Extraction Intégrale :** Extrais **systématiquement et intégralement TOUTES** les questions présentes dans le PDF 2, **sans exception**. Ignore toute numérotation (ex: "1.", "Q1.") associée aux questions lors de l'extraction du texte de la question elle-même.
                        * Pour **chaque** question extraite : Extrais **toutes** les propositions de réponse qui lui sont associées dans le PDF 2. Ignore toute lettre ou numéro (ex: "a)", "1)") associé aux options lors de l'extraction du texte de l'option elle-même.

                    3.  **Validation et Enrichissement via le Cours (PDF 1) :**
                        * Pour **chaque** question extraite du PDF 2 :
                            * **Recherche Approfondie dans PDF 1 :** Pour déterminer la ou les bonnes réponses et fournir la justification, consulte **l'intégralité** du contenu du PDF 1 (Cours). Ne te limite **jamais** aux premières pages ou sections. Tu dois chercher partout où l'information pertinente pourrait se trouver.
                            * **Identification de la/des Bonne(s) Réponse(s) :** En te basant **strictement et uniquement** sur les informations présentes dans le PDF 1, identifie parmi les options extraites du PDF 2 pour cette question, **la ou les option(s)** qui sont factuellement correctes.
                                * **Important :** Il peut y avoir une seule bonne réponse (QCU) ou plusieurs bonnes réponses (QCM). Ta tâche est de trouver toutes celles qui sont correctes selon PDF 1.
                                * Récupère le **texte exact et complet** de chaque option correcte identifiée.
                            * **Génération de l'Explication :** Rédige une **explication claire, précise et concise** (en français) qui justifie pourquoi la ou les réponse(s) sélectionnée(s) est/sont correcte(s). Cette explication doit se fonder **exclusivement** sur les concepts, faits, données ou raisonnements présents dans le PDF 1. Ne fais **aucune** inférence non supportée par le PDF 1.
                            * **Sourçage Rigoureux dans PDF 1 :** Pour chaque question, fournis une référence **précise et vérifiable** dans le PDF 1 qui justifie **sans ambiguïté** la ou les réponses correctes. Indique :
                                * Le **numéro de page exact** dans le PDF 1.
                                * La **section/le concept clé/le texte spécifique/l'image/le tableau pertinent(s)** du PDF 1 utilisé(s) pour la justification.

                    4.  **Formatage de la Sortie JSON :**
                        * Structure **l'intégralité** de la sortie conformément au **schéma JSON défini précédemment** (celui utilisé pour la génération de quiz, avec `emoji`, `title`, `questions` [{`question`, `answers`, `correct`, `explanation`, `sources` [{`source`, `page`}]}]).
                        * La liste `questions` dans le JSON contiendra **toutes** les questions extraites du PDF 2, dans l'ordre où elles apparaissent dans ce PDF 2, mais enrichies avec les réponses correctes, explications et sources validées via le PDF 1.
                        * Le champ `correct` dans chaque objet question contiendra une liste contenant le texte exact d'une ou plusieurs options correctes.
                        * Le titre et l'emoji déterminés à partir du PDF 1 doivent être placés dans les champs `title` et `emoji` à la racine du JSON.

                    **Points Cruciaux à Respecter :**
                    * **Fidélité Absolue au PDF 1 :** La validation des réponses et la génération des explications/sources dépendent **exclusivement** du contenu du PDF 1.
                    * **Exhaustivité pour PDF 2 :** **Aucune** question ou option présente dans le PDF 2 ne doit être omise lors de l'extraction.
                    * **Pas de numérotation héritée :** Le texte extrait pour les questions et les réponses ne doit pas inclure les numéros ou lettres originaux du PDF 2.
                    * **Clarté et Précision :** Les explications et les sources doivent être claires, précises et directement liées au contenu du PDF 1.                         
                
                    """)
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            top_k=40,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            max_output_tokens=65536,
            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                required=["status", "message"],
                properties={
                    "status": genai.types.Schema(
                        type=genai.types.Type.STRING,
                        description="État de la requête: SUCCESS ou ERROR",
                    ),
                    "message": genai.types.Schema(
                        type=genai.types.Type.STRING,
                        description="Message d'erreur si status=ERROR",
                    ),
                    "emoji": genai.types.Schema(
                        type=genai.types.Type.STRING,
                        description="Emoji représentant le thème du quiz",
                    ),
                    "title": genai.types.Schema(
                        type=genai.types.Type.STRING,
                        description="Titre du quiz extrait",
                    ),
                    "questions": genai.types.Schema(
                        type=genai.types.Type.ARRAY,
                        description="Liste des questions extraites",
                        items=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=["question", "answers", "correct", "explanation", "sources", "type_question"],
                            properties={
                                "question": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                    description="Texte de la question",
                                ),
                                "type_question": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                    description="Type de question: 'connaissance' ou 'application'",
                                    enum=["connaissance", "application"]
                                ),
                                "answers": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    description="Liste des réponses possibles",
                                    items=genai.types.Schema(
                                        type=genai.types.Type.STRING,
                                    ),
                                ),
                                "correct": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    description="Liste des réponses correctes",
                                    items=genai.types.Schema(
                                        type=genai.types.Type.STRING,
                                    ),
                                ),
                                "explanation": genai.types.Schema(
                                    type=genai.types.Type.STRING,
                                    description="Explication de la réponse correcte",
                                ),
                                "sources": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    description="Liste des sources dans le cours",
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=["source", "page"],
                                        properties={
                                            "source": genai.types.Schema(
                                                type=genai.types.Type.STRING,
                                                description="Source de la question",
                                            ),
                                            "page": genai.types.Schema(
                                                type=genai.types.Type.INTEGER,
                                                description="Numéro de page de la source",
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    ),
                },
            ),
        )

        output = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            output += chunk.text
            
        response_data = json.loads(output)
        logging.debug(f"API Response: {response_data}")
        
        if response_data.get('status') == 'ERROR':
            os.remove(course_temp_path)
            os.remove(quizz_temp_path)
            return jsonify({'success': False, 'error': response_data.get('message')})
        
        pastel_colors = [
            "#FFFBF2", "#FFF5E1", "#FAF3DD", "#F3E8EE", "#E8F8F5",
            "#E3F2FD", "#F8E8FF", "#FDF8F5", "#F0F8FF", "#FCF5E5"
        ]

        # Préparer les données du quiz
        quiz_title = response_data.get('title', 'Quiz extrait')
        course_name = os.path.splitext(course_pdf.filename)[0]
        
        quizz_data[quizz_id] = {
            'title': quiz_title,
            'name': course_name,
            'emoji': response_data.get('emoji', '📝'),
            'level': 'Non spécifié',
            'type': 'QCM',
            'notation': quizz_notation,
            'notions': 'Extraites de l\'annale',
            'size': len(response_data.get('questions', [])),
            'color': random.choice(pastel_colors),
            'quizzes': [
                {
                    'id': random.randint(1000000000000000, 9999999999999999),
                    'date': get_paris_time().strftime('%Y-%m-%d'),
                    'questions': response_data.get('questions', []),
                    'attempts': []
                }
            ]
        }
        
        # Sauvegarder les fichiers
        user_files_dir = os.path.join(app.root_path, 'static', 'user_files')
        os.makedirs(user_files_dir, exist_ok=True)
        user_file_path = os.path.join(user_files_dir, f'file_quizz_{quizz_id}.pdf')
        shutil.copy2(course_temp_path, user_file_path)
        
        # Créer une prévisualisation du PDF
        pdf_preview_dir = os.path.join(app.root_path, 'static', 'pdf_preview')
        os.makedirs(pdf_preview_dir, exist_ok=True)
        pdf_preview_path = os.path.join(pdf_preview_dir, f'preview_{quizz_id}.jpg')
        images = convert_from_path(user_file_path)
        images[0].save(pdf_preview_path, 'JPEG')

        # Enregistrer les données dans le JSON
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as file:
            json.dump(quizz_data, file, indent=4)
        
        # Nettoyer les fichiers temporaires
        os.remove(course_temp_path)
        os.remove(quizz_temp_path)
        
        # Mettre à jour le dossier
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
            
        def add_quizz_to_folder(folders, folder_id):
            for folder in folders:
                if folder['id'] == folder_id:
                    folder['quizzes'].append(quizz_id)
                    return True
            if add_quizz_to_folder(folder['folders'], folder_id):
                return True
            return False
        add_quizz_to_folder([folder_data], session['folder_id'])
        
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'w') as folder_file:
            json.dump(folder_data, folder_file, indent=4)
        
        folder_id = session['folder_id']
        del session['folder_id']
        
        response = make_response(jsonify({'success': True, 'quizz_id': quizz_id, 'folder_id': folder_id}))
        response.set_cookie('user_data', json.dumps(quizz_data), max_age=31536000)
        return response
    except Exception as e:
        logging.error(e)
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/quizz/<int:quizz_id>', methods=['GET'])
@login_required
def quizz(quizz_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        quizz = data[str(quizz_id)]
        
        data_to_show = {
            'id': quizz_id,
            'title': quizz['title'],
            'color': quizz['color'],
            'emoji': quizz['emoji'],
            'size': quizz['size'],
            'preview_path': url_for('static', filename=f'pdf_preview/preview_{quizz_id}.jpg'),
            'pdf_path': url_for('static', filename=f'user_files/file_quizz_{quizz_id}.pdf'),
            'quizz_amount': len(quizz['quizzes']),
            'quizzes': quizz['quizzes']
        }
        
        # Find the id of the folder where the quizz is located
        with open(os.path.join(app.root_path, 'static', 'folder.json'), 'r') as folder_file:
            folder_data = json.load(folder_file)
        def find_quizz_in_folder(folders, quizz_id):
            for folder in folders:
                if quizz_id in folder['quizzes']:
                    return folder['id']
                if 'folders' in folder:
                    found = find_quizz_in_folder(folder['folders'], quizz_id)
                    if found:
                        return found
            return None
        folder_id = find_quizz_in_folder([folder_data], quizz_id)
        
        return render_template('quizz.html', data=data_to_show, folder_id=folder_id)
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))
    
@app.route('/quizz/<int:quizz_id>/generate', methods=['POST'])
@login_required
def generate_quizz(quizz_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        quizz = data[str(quizz_id)]
        
        client =genai.Client(api_key=os.environ['GEMINI_API_KEY'])
        
        files = [
            client.files.upload(file=os.path.join(app.root_path, 'static', 'user_files', f'file_quizz_{quizz_id}.pdf'))
        ]
        
        model = "gemini-2.5-flash-preview-04-17"
        
        contents = [
            types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                file_uri=files[0].uri,
                mime_type=files[0].mime_type,
                ),
                types.Part.from_text(text=f"""
                **Objectif Principal :** Générer un quiz de **{quizz['size']} questions** évaluant la compréhension **approfondie** et la **capacité d'application/raisonnement** basées **UNIQUEMENT et EXCLUSIVEMENT** sur le contenu du document PDF fourni. Agis comme un expert du domaine dont la **SEULE** source de vérité est ce document.

                **Règle Fondamentale :** **AUCUNE connaissance extérieure** ne doit être utilisée, ni pour formuler les questions, ni pour déterminer les bonnes réponses ou les distracteurs. Le PDF est la référence absolue et unique.

                **Instructions Détaillées :**

                1.  **Couverture du Document :** Assure-toi que les questions couvrent **l'intégralité du document** (du début à la fin), reflétant une compréhension globale et pas seulement des premières sections. Ne te limite pas aux titres ou aux introductions de section.

                2.  **Format et Structure du Quiz :**
                    * Le quiz doit être au format **{quizz['type']}**.
                    * **Choix Multiple (si applicable) :**
                        * **TOUTES** les questions à choix multiples DOIVENT comporter **PLUSIEURS réponses correctes**.
                        * Propose un total de **4 à 6 options** par question (incluant bonnes réponses et distracteurs pertinents).
                    * **Mixte (si applicable) :** Inclut un **mélange équilibré** de questions à réponse unique et de questions à réponses multiples (respectant la règle ci-dessus).
                    * **Questions Spécifiant un Nombre :** Même si une question demande "Quels sont les 2 avantages...", propose **TOUJOURS plus d'options** (ex: 4 ou 5 au total), forçant l'identification des bonnes réponses parmi un ensemble plus large de distracteurs plausibles issus du PDF.
                    * **Identification des Bonnes Réponses :** Indique les bonnes réponses en reprenant **TEXTUELLEMENT** leur contenu exact (leurs valeurs). **JAMAIS** de lettres ou de positions (ex : "Les bonnes réponses sont : 'Concept A tel que décrit', 'Méthode B expliquée page X'.").
                    * **Présentation :** Ne numérote **NI** les questions, **NI** les options. Présente-les simplement séquentiellement.
                    * **Ordre :** L'ordre des questions doit être **aléatoire** et ne **PAS** suivre l'ordre du document.

                3.  **Contenu et Style des Questions :**
                    * **INSTRUCTION CRITIQUE - Formulation Directe :** NE JAMAIS utiliser de tournures comme "Selon le document...", "D'après le PDF...". Pose les questions **directement**, comme à un étudiant qui **maîtrise le contenu du PDF**. Le PDF est la référence factuelle **implicite**. (Ex: Au lieu de "Selon le PDF, comment définir X ?", demande "Comment X est-il défini ?" ou "Quelles caractéristiques définissent X ?").
                    * **Système de Notation :** Applique le système suivant : **{quizz['notation']}**.
                    * **Notions Obligatoires :** Intègre **impérativement** des questions (idéalement d'application/raisonnement) sur : **{quizz['notions']}**.
                    * **VARIÉTÉ et PROFONDEUR (Instruction Clé) :**
                        * **Mix de Styles :** Va au-delà du simple rappel. Inclus des questions demandant :
                            * **Identification/Classification :** Reconnaître des concepts, types, catégories décrits.
                            * **Comparaison/Contraste :** Analyser les similarités/différences entre méthodes/théories du PDF.
                            * **Analyse de Cause/Effet :** Identifier les liens de causalité expliqués dans le PDF.
                            * **Application de Procédure/Méthode :** Suivre les étapes d'un processus décrit dans le PDF.
                            * **Calcul/Interprétation :** Utiliser une formule ou interpréter des données/graphiques présentés dans le PDF.
                        * **FOCUS MAJEUR - Application & Raisonnement (Vise 20-35% du quiz) :** Ces questions doivent exiger **plus qu'une simple récupération d'information**. Elles doivent tester la capacité à **utiliser activement, combiner, et inférer** à partir des connaissances du PDF.
                            * **Crée des Mini-Scénarios ou Problèmes :** Propose des situations **concrètes et plausibles**, des **études de cas très simplifiées**, ou des **ensembles de données**, TOUJOURS **strictement inspirés ou conformes** aux exemples, contextes ou types de données présents dans le PDF.
                            * **Formulation des Questions d'Application :**
                                * "Face à [Scénario basé sur le PDF], quelle serait l'approche prioritaire en utilisant les principes de [Concept du PDF] ?"
                                * "Analysez ces [Type de données comme dans le PDF] : quelle(s) conclusion(s) spécifique(s) peut-on tirer concernant [Phénomène décrit dans le PDF], en se basant **uniquement** sur les éléments fournis dans le document ?"
                                * "Étant donné [Paramètres spécifiques issus du PDF], quel serait le résultat de l'application de la méthode [Nom méthode du PDF] ?"
                                * "Quel(s) outil(s) ou critère(s) **décrit(s) dans ce document** serai(en)t le(s) plus pertinent(s) pour évaluer/résoudre [Problème spécifique formulé avec les termes du PDF] ? Pourquoi (selon le PDF) ?"
                                * "Si l'on modifie le paramètre X comme suit [Variation plausible selon le PDF], quel impact cela aurait-il sur Y, d'après les mécanismes expliqués dans le document ?"
                            * **Exigence Clé :** La question doit obliger à **mobiliser et appliquer** une ou plusieurs informations/méthodes du PDF pour trouver la réponse, pas seulement à la localiser. Pense "Que ferait quelqu'un qui a *compris et intégré* ce passage du PDF face à cette situation ?".

                4.  **Qualité des Options et Distracteurs :**
                    * **Toutes** les options (correctes et incorrectes) doivent être **plausibles** dans le contexte du PDF.
                    * Les distracteurs doivent être **pertinents** mais **clairement faux ou non supportés par le contenu spécifique du PDF**. Ils peuvent représenter des erreurs communes *discutées ou implicitement contredites* dans le document, ou des concepts proches mais distincts.
                    * Équilibre la longueur et le style des options.

                5.  **Positionnement Aléatoire des Réponses :** Pour chaque question, la ou les bonnes réponses doivent être positionnées **aléatoirement** parmi les options. Évite toute tendance systématique.

                6.  **Sourçage et Justification Rigoureux (Pour CHAQUE question) :**
                    * **Page(s) Exacte(s) :** Indique le numéro de page précis dans le PDF.
                    * **Concept(s) Clé(s) / Passage(s) Pertinent(s) :** Référence le texte, l'image, le tableau, la formule qui **justifie SANS AMBIGUÏTÉ la question ET la ou les bonnes réponses**.
                    * **Justification d'Application :** Pour les questions d'application/raisonnement, la référence doit pointer vers le(s) principe(s), méthode(s) ou information(s) du PDF qui sont **directement mobilisés ou combinés** pour répondre correctement au scénario/problème posé. La justification doit expliquer *comment* le PDF mène à la bonne réponse et invalide les distracteurs.

                *(Meta-instruction interne pour l'IA : Lors de la création des questions d'application, décompose le raisonnement : 1. Identifier le concept/méthode clé du PDF à tester. 2. Créer un scénario/problème qui nécessite l'application de ce concept/méthode, en utilisant uniquement des éléments/contextes présents ou implicites dans le PDF. 3. Déterminer la ou les réponses correctes en appliquant strictement le PDF. 4. Créer des distracteurs plausibles mais réfutables par le PDF.)*
                
                """),
            ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.3, # Garder une certaine créativité mais la rigueur vient des instructions
            top_p=0.95,
            top_k=40,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            max_output_tokens=65536,
            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type = genai.types.Type.OBJECT,
                required = ["emoji", "title", "questions"],
                properties = {
                    "emoji": genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "Emoji pertinent représentant le sujet principal du quiz.",
                    ),
                    "title": genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "Titre concis et informatif pour le quiz, basé sur le sujet du PDF.",
                    ),
                    "questions": genai.types.Schema(
                        type = genai.types.Type.ARRAY,
                        description = "Liste des questions composant le quiz.",
                        items = genai.types.Schema(
                            type = genai.types.Type.OBJECT,
                            required = ["question", "answers", "correct", "explanation", "sources", "type_question"],
                            properties = {
                                "question": genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                    description = "Texte de la question, formulé directement (SANS 'Selon le document...'), évaluant la compréhension ou l'application du contenu du PDF.",
                                ),
                                "type_question": genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                    description = "Type de question: 'connaissance' ou 'application'",
                                    enum = ["connaissance", "application"]
                                ),
                                "answers": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste des réponses possibles (options). Doit inclure les réponses correctes et des distracteurs plausibles mais incorrects selon le PDF. Viser 4-6 options au total.",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                ),
                                "correct": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste contenant UNIQUEMENT le texte exact (valeur textuelle) de la ou des réponses correctes, telles qu'elles apparaissent dans la liste 'answers'.",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                ),
                                "explanation": genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                    description = "Explication concise justifiant pourquoi la/les réponse(s) sont correctes, en se référant explicitement aux concepts ou informations du PDF.",
                                ),
                                "sources": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste des références précises dans le PDF justifiant la question et la/les réponses correctes.",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.OBJECT,
                                        required = ["source", "page"],
                                        properties = {
                                            "source": genai.types.Schema(
                                                type = genai.types.Type.STRING,
                                                description = "Concept clé, section, ou élément spécifique du PDF (ex: 'Définition du Modèle X', 'Tableau 3.1', 'Méthode de calcul Y') justifiant la réponse.",
                                            ),
                                            "page": genai.types.Schema(
                                                type = genai.types.Type.INTEGER,
                                                description = "Numéro de page exact dans le PDF où trouver la justification.",
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    ),
                },
            ),
            system_instruction=[
                types.Part.from_text(text=f"""**Contexte Impératif :** Positionne-toi comme un(e) enseignant(e) spécialiste rigoureux de {quizz['name']}, 
                    créant une évaluation pour des étudiants de niveau {quizz['level']}. Ton objectif UNIQUE est de créer un quiz qui évalue **précisément et 
                    exclusivement** la compréhension et la capacité d'application du contenu du PDF fourni. Tu ne dois utiliser **AUCUNE autre information ou connaissance**. 
                    La **fidélité absolue** au document source et la **pertinence pédagogique** des questions et des distracteurs (basés uniquement sur le PDF) sont tes priorités 
                    absolues. Le quiz doit servir d'outil fiable de validation et de renforcement, reflétant uniquement le matériel de cours présenté.
                    **OBLIGATION FORMELLE:** Au moins 20% (MAX 35%) des questions générées DOIVENT être des questions d'application/raisonnement 
                    avec des mini-scénarios concrets. Tu dois alterner systématiquement entre questions de connaissance et questions d'application.
                    N'inclus surtout pas dans tes questions avec "Selon le PDF..." ou "D'après le document...".
                """),
            ],
        )
        
        output = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            output += chunk.text
            
        output = json.loads(output)
        logging.debug(f"API Response: {output}")
        
        # Verify if 'correct' answers are in 'answers', and handle mismatches
        for question in output['questions']:
            valid_correct_answers = []
            for correct in question['correct']:
                if correct in question['answers']:
                    valid_correct_answers.append(correct)
                else:
                    # Check for close matches in 'answers'
                    close_matches = get_close_matches(correct, question['answers'], n=1, cutoff=0.9)
                    if close_matches:
                        valid_correct_answers.append(close_matches[0])
            question['correct'] = valid_correct_answers
        
        quizz['quizzes'].append({
            'id': random.randint(1000000000000000, 9999999999999999),
            'date': get_paris_time().strftime('%Y-%m-%d'),
            'questions': output['questions'],
            'attempts': []
        })
        
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as file:
            json.dump(data, file, indent=4)
            
        response = make_response(jsonify({'success': True}))
        response.set_cookie('user_data', json.dumps(data), max_age=31536000)
        return response
    except Exception as e:
        logging.error(e)
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/quizz/<int:id>/play/<int:quizz_id>', methods=['GET'])
@login_required
def play_quizz(id, quizz_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        if str(id) not in data or not any(q['id'] == quizz_id for q in data[str(id)]['quizzes']):
            return redirect(url_for('index'))
        
        game_session_id = random.randint(1000000000000000, 9999999999999999)
        expire_date = get_paris_time() + timedelta(hours=2)
        
        session['game_session'] = {
            'id': game_session_id,
            'title': data[str(id)]['title'],
            'quizz_id': id,
            'color': data[str(id)]['color'],
            'quizz_version_id': quizz_id,
            'expire_date': expire_date.strftime('%Y-%m-%d %H:%M:%S'),
            'date_start': get_paris_time().strftime('%Y-%m-%d %H:%M:%S'),
            'questions': [
                {
                    'question': q['question'][3:] if q['question'][:3].isdigit() and q['question'][2] == '.' else q['question'],
                    'answers': q['answers'],
                    'correct': q['correct'],
                    'type_question': q['type_question'],
                    'answered': False,
                    'selected_answers': []
                } for q in next(q for q in data[str(id)]['quizzes'] if q['id'] == quizz_id)['questions']
            ]
        }
        
        logging.debug(f"Quizz Data JSON: {session['game_session']}")
        return redirect(url_for('play', game_session_id=game_session_id, question=0))
    except Exception as e:
        logging.error(e)
        flash('Une erreur est survenue', 'error')
        return redirect(url_for('index'))

@app.route('/play/<int:game_session_id>/<int:question>', methods=['GET', 'POST'])
@login_required
def play(game_session_id, question):
    try:
        if 'game_session' not in session or int(session['game_session']['id']) != int(game_session_id):
            flash('Session invalide', 'error')
            return redirect(url_for('index'))
        elif get_paris_time() > parse_datetime_with_tz(session['game_session']['expire_date']):
            flash('Session expirée', 'error')
            return redirect(url_for('index'))
        elif question < 0 or question >= len(session['game_session']['questions']):
            flash('Question invalide', 'error')
            return redirect(url_for('play', game_session_id=game_session_id, question=0))
        
        question_data = session['game_session']['questions']
        
        if question < 0 or question >= len(question_data):
            flash('Question invalide', 'error')
            return redirect(url_for('play', game_session_id=game_session_id, question=0))
                
        if request.method == 'POST':
            question_id = int(request.form['question_id'])
            
            if int(request.form['end']) == 0:
                end = False
            else:
                end = True
                
            if 'choice' not in request.form and 'choice[]' not in request.form:
                answer = []
            else:
                if len(question_data[question_id]['correct']) == 1:
                    answer = [request.form['choice']]
                else:
                    answer = request.form.getlist('choice[]')
                
                question_data[question_id]['answered'] = True
                question_data[question_id]['selected_answers'] = answer
        
            session['game_session']['questions'] = question_data
            
            if end:
                return redirect(url_for('end', game_session_id=game_session_id))
            
            
            
        date_start = parse_datetime_with_tz(session['game_session']['date_start'])
                    
        return render_template('play.html', 
                               id=session['game_session']['id'], 
                               title=session['game_session']['title'],
                               question=question, 
                               color=session['game_session']['color'], 
                               date_start=date_start,
                               question_data=question_data)
    except Exception as e:
        logging.error(e)
        flash('Une erreur est survenue', 'error')
        return redirect(url_for('index'))
    
@app.route('/play/<int:game_session_id>/end', methods=['GET'])
@login_required
def end(game_session_id):
    try:
        if 'game_session' not in session or int(session['game_session']['id']) != int(game_session_id):
            flash('Session invalide',
                  'error')
            return redirect(url_for('index'))
        elif get_paris_time() > parse_datetime_with_tz(session['game_session']['expire_date']):
            flash('Session expirée', 'error')
            return redirect(url_for('index'))

        question_data = session['game_session']['questions']            
                
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
            
        quizz = data[str(session['game_session']['quizz_id'])]
        
        score = 0
        for q in question_data:            
            selected_answer_text = []
            for a in q['selected_answers']:
                selected_answer_text.append(q['answers'][int(a)])
                
            if selected_answer_text:
                if set(q['correct']) == set(selected_answer_text):
                    score += 1
                else:
                    if quizz['notation'] == 'Points négatifs':
                        score -= 1
        
        data_to_insert = {
            'id': random.randint(1000000000000000, 9999999999999999),
            'date': get_paris_time().strftime('%Y-%m-%d'),
            'score': score,
            'answer': [
                [int(a) for a in q['selected_answers']] for q in question_data
            ]
        }
        
        # Find into quizzes where id=quizz_version_id
        quizz_version = next(q for q in quizz['quizzes'] if int(q['id']) == int(session['game_session']['quizz_version_id']))
        
        # Append the new attempt
        quizz_version['attempts'].append(data_to_insert)
                
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as file:
            json.dump(data, file, indent=4)
                        
        quizz_id = session['game_session']['quizz_id']
        quizz_version_id = session['game_session']['quizz_version_id']
        attempt_id = data_to_insert['id']
            
        del session['game_session']
            
        response = make_response(redirect(url_for('attempt', quizz_id=quizz_id, quizz_version_id=quizz_version_id, attempt_id=attempt_id)))
        response.set_cookie('user_data', json.dumps(data), max_age=31536000)
        return response
    except Exception as e:
        logging.error(e)
        flash('Une erreur est survenue', 'error')
        return redirect(url_for('index'))
    
@app.route('/quizz/<int:quizz_id>/attempt/<int:quizz_version_id>/<int:attempt_id>', methods=['GET'])
@login_required
def attempt(quizz_id, quizz_version_id, attempt_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        quizz = data[str(quizz_id)]
        quizz_version = next(q for q in quizz['quizzes'] if q['id'] == quizz_version_id)
        attempt = next(a for a in quizz_version['attempts'] if a['id'] == attempt_id)
        
        index_of_right_answers = []
        
        for i in range(len(quizz_version['questions'])):
            questions_selected = []
            for a in attempt['answer'][i]:
                questions_selected.append(quizz_version['questions'][i]['answers'][int(a)])
                        
            if set(quizz_version['questions'][i]['correct']) == set(questions_selected):
                index_of_right_answers.append(i)
                        
        data_to_show = {
            'id': quizz_id,
            'version_id': quizz_version_id,
            'title': quizz['title'],
            'doc_url': url_for('static', filename=f'user_files/file_quizz_{quizz_id}.pdf'),
            'type': quizz['type'],
            'notation': quizz['notation'],
            'type': quizz['type'],
            'color': quizz['color'],
            'score': attempt['score'],
            'date': attempt['date'],
            'questions': quizz_version['questions'],
            'answers': attempt['answer'],
            'correct_answers_index': index_of_right_answers
        }
        
        logging.debug(f"Attempt Data JSON: {data_to_show}")
        
        return render_template('attempt.html', data=data_to_show)
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))

@app.route('/update_report', methods=['GET'])
@login_required
def update_report():
    def get_recent_remote_commits(n=20, branch="origin/main"):
        try:
            # Format : hash|auteur|date|message
            format_str = "%h|%an|%ad|%s"
            result = subprocess.run(
                ["git", "log", branch, f"-n{n}", f"--pretty=format:{format_str}", "--date=format:%Y-%m-%d %H:%M:%S"],
                capture_output=True,
                text=True,
                check=True
            )
            raw_commits = result.stdout.strip().split("\n")
            commits = []
            for entry in raw_commits:
                parts = entry.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
            return commits
        except subprocess.CalledProcessError:
            return [{"hash": "Erreur", "author": "-", "date": "-", "message": "Impossible de récupérer les commits."}]

    return render_template('update_report.html', commits=get_recent_remote_commits())

@app.route('/report', methods=['GET'])
@login_required
def report():
    def get_recent_logs(minutes=2, log_file="app.log"):
        logs = []
        try:
            time_threshold = datetime.now() - timedelta(minutes=minutes)
            with open(log_file, "r") as f:
                for line in f:
                    try:
                        # Extrait la date du début de ligne (doit correspondre à `datefmt`)
                        timestamp_str = line.split(" | ")[0]
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if timestamp >= time_threshold:
                            logs.append(line.strip())
                    except Exception:
                        continue
        except FileNotFoundError:
            logs.append("Fichier de log introuvable.")
        return logs
    
    logs = get_recent_logs()
    if not logs:
        body = "Aucun log généré dans les 2 dernières minutes."
    else:
        body = "Description du problème (Optionel) :\n<=======================================>\n<======= INCLURE UNE DESCRIPTION =======>\n<=======================================>\n Logs récents (2 dernières minutes):\n\n" + "\n".join(logs)

    mailto_link = (
        "mailto:dev.hpktz@gmail.com"
        "?subject=" + quote("Rapport automatique - Logs récents") +
        "&body=" + quote(body)
    )
    
    return redirect(mailto_link)
    

@app.route('/stop', methods=['GET'])
@login_required
def stop():
    # Stop the flask app and close the browser tab
    import os, signal
    pid = os.getpid()
    # Return HTML with JavaScript to close the tab before killing the process
    html = render_template('stop_server.html')
    # Use a short delay to give the browser time to process the close command
    def shutdown():
        import time
        time.sleep(0.5)
        os.kill(pid, signal.SIGTERM)
        
    import threading
    threading.Thread(target=shutdown).start()
    
    return html


if __name__ == '__main__':
    app.run(debug=True)
