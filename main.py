from flask import Flask, request, jsonify, render_template, session, url_for, redirect
import os
import random
import logging
import json

from google import genai
from google.genai import types

from pdf2image import convert_from_path

import base64
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

secret_key = os.urandom(24)
app.secret_key = secret_key

@app.route('/', methods=['GET'])
def index():
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        data_to_show = []
        
        if 'quizz' in request.args: 
            query = int(request.args.get('quizz'))
        else:
            query = 0
        
        print(query)
        
        for key in data:        
            data_to_show.append({
                'id': key,
                'title': data[key]['title'],
                'color': data[key]['color'],
                'emoji': data[key]['emoji'],
                'size': data[key]['size'],
                'preview_path': url_for('static', filename=f'pdf_preview/preview_{key}.jpg'),
                'quizz_amount': len(data[key]['quizzes']),
                'last_attempt': "...", 
                'to_highlight': True if int(key) == query else False
            })
        
        return render_template('home.html', data=data_to_show)
    except Exception as e:
        logging.error(e)
        return render_template('home.html', data=[])

@app.route('/create/1', methods=['GET'])
def create1():
    return render_template('creation-step1.html')

@app.route('/create/2', methods=['POST'])
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
        
        model = "gemini-2.0-flash"
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=files[0].uri,
                        mime_type=files[0].mime_type,
                    ),
                    types.Part.from_text(text=f"""Instructions :
                    - Génère un quiz de {session['quizz_size']} questions en te basant uniquement sur le contenu du PDF fourni.
                    - Le quiz doit être au format {session['quizz_type']}.
                    - Applique un système de notation {session['quizz_notation']}.
                    - Intègre obligatoirement des questions sur les notions spécifiques suivantes : {session['quizz_notions']}.
                    - Formule des questions variées, allant des notions de base aux concepts avancés, pour tester la compréhension et la réflexion critique des étudiants.
                    - Assure-toi que les propositions de réponse sont crédibles et bien équilibrées, avec des distracteurs pertinents."""),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type = genai.types.Type.OBJECT,
                required = ["emoji", "title", "questions"],
                properties = {
                    "emoji": genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "Emoji représentant l'objet",
                    ),
                    "title": genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "Titre du quiz",
                    ),
                    "questions": genai.types.Schema(
                        type = genai.types.Type.ARRAY,
                        description = "Liste des questions",
                        items = genai.types.Schema(
                            type = genai.types.Type.OBJECT,
                            required = ["question", "answers", "correct"],
                            properties = {
                                "question": genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                    description = "Texte de la question",
                                ),
                                "answers": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste des réponses possibles",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                ),
                                "correct": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste des réponses correctes (peut contenir les valeurs ou les index)",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                ),
                            },
                        ),
                    ),
                },
            ),
            system_instruction=[
                types.Part.from_text(text=f"""Contexte : Tu es un expert dans le domaine de {session['course_name']}, et tu es enseignant(e) à 
            un niveau {session['course_level']}. Ton objectif est d’évaluer les compétences des étudiants à 
            travers un quiz rigoureux et pertinent basé exclusivement sur le contenu du cours fourni en PDF.
            Format attendu :
            - Chaque question doit être numérotée.
            - Pour les QCM et choix unique, indique clairement les bonnes réponses.
            - Pour chaque question, ajoute une courte justification/explanation pour renforcer l’apprentissage. """),
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
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'questions': output['questions'],
                    'attempts': []
                }
            ]
        }
        
        user_files_dir = os.path.join(app.root_path, 'static', 'user_files')
        os.makedirs(user_files_dir, exist_ok=True)
        user_file_path = os.path.join(user_files_dir, f'file_quizz_{quizz_id}.pdf')
        os.rename(session['course_pdf'], user_file_path)
        
        pdf_previw_dir = os.path.join(app.root_path, 'static', 'pdf_preview')
        os.makedirs(pdf_previw_dir, exist_ok=True)
        pdf_preview_path = os.path.join(pdf_previw_dir, f'preview_{quizz_id}.jpg')
        images = convert_from_path(user_file_path)
        images[0].save(pdf_preview_path, 'JPEG')

        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as file:
            json.dump(quizz, file, indent=4)

        return jsonify({'success': True, 'quizz_id': quizz_id})
    except Exception as e:
        logging.error(e)
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/quizz/<int:quizz_id>', methods=['GET'])
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
            'quizz_amount': len(quizz['quizzes'])
        }
        
        return render_template('quizz.html', data=data_to_show)
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))
    
@app.route('/quizz/<int:quizz_id>/generate', methods=['POST'])
def generate_quizz(quizz_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        quizz = data[str(quizz_id)]
        
        client =genai.Client(api_key=os.environ['GEMINI_API_KEY'])
        
        files = [
            client.files.upload(file=os.path.join(app.root_path, 'static', 'user_files', f'file_quizz_{quizz_id}.pdf'))
        ]
        
        model = "gemini-2.0-flash"
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=files[0].uri,
                        mime_type=files[0].mime_type,
                    ),
                    types.Part.from_text(text=f"""Instructions :
                    - Génère un quiz de {quizz['size']} questions en te basant uniquement sur le contenu du PDF fourni.
                    - Le quiz doit être au format {quizz['type']}.
                    - Applique un système de notation {quizz['notation']}.
                    - Intègre obligatoirement des questions sur les notions spécifiques suivantes : {quizz['notions']}.
                    - Formule des questions variées, allant des notions de base aux concepts avancés, pour tester la compréhension et la réflexion critique des étudiants.
                    - Assure-toi que les propositions de réponse sont crédibles et bien équilibrées, avec des
                    distracteurs pertinents."""),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type = genai.types.Type.OBJECT,
                required = ["emoji", "title", "questions"],
                properties = {
                    "emoji": genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "Emoji représentant l'objet",
                    ),
                    "title": genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "Titre du quiz",
                    ),
                    "questions": genai.types.Schema(
                        type = genai.types.Type.ARRAY,
                        description = "Liste des questions",
                        items = genai.types.Schema(
                            type = genai.types.Type.OBJECT,
                            required = ["question", "answers", "correct"],
                            properties = {
                                "question": genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                    description = "Texte de la question",
                                ),
                                "answers": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste des réponses possibles",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                ),
                                "correct": genai.types.Schema(
                                    type = genai.types.Type.ARRAY,
                                    description = "Liste des réponses correctes (peut contenir les valeurs ou les index)",
                                    items = genai.types.Schema(
                                        type = genai.types.Type.STRING,
                                    ),
                                ),
                            },
                        ),
                    ),
                },
            ),
            system_instruction=[
                types.Part.from_text(text=f"""Contexte : Tu es un expert dans le domaine de {quizz['name']}, et tu es enseignant(e) à 
            un niveau {quizz['level']}. Ton objectif est d’évaluer les compétences des étudiants à 
            travers un quiz rigoureux et pertinent basé exclusivement sur le contenu du cours fourni en PDF.
            Format attendu :
            - Chaque question doit être numérotée.
            - Pour les QCM et choix unique, indique clairement les bonnes réponses.
            - Pour chaque question, ajoute une courte justification/explanation pour renforcer
            l’apprentissage. """),
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
        
        quizz['quizzes'].append({
            'id': random.randint(1000000000000000, 9999999999999999),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'questions': output['questions'],
            'attempts': []
        })
        
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as file:
            json.dump(data, file, indent=4)
            
        return jsonify({'success': True})
    except Exception as e:
        logging.error(e)
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
