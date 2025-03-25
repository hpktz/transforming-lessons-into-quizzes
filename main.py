from flask import Flask, request, jsonify, render_template, session, url_for, redirect, flash
from flask_session import Session
import os
import random
import logging
import json

from google import genai
from google.genai import types

from pdf2image import convert_from_path

import base64
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

secret_key = os.urandom(24)
app.secret_key = secret_key

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

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
    
@app.route('/delete/<int:quizz_id>', methods=['GET'])
def delete(quizz_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        del data[str(quizz_id)]
        
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'w') as file:
            json.dump(data, file, indent=4)
        
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))

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
            'quizz_amount': len(quizz['quizzes']),
            'quizzes': quizz['quizzes']
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
    
@app.route('/quizz/<int:id>/play/<int:quizz_id>', methods=['GET'])
def play_quizz(id, quizz_id):
    try:
        with open(os.path.join(app.root_path, 'static', 'user_data.json'), 'r') as file:
            data = json.load(file)
        
        if str(id) not in data or not any(q['id'] == quizz_id for q in data[str(id)]['quizzes']):
            return redirect(url_for('index'))
        
        game_session_id = random.randint(1000000000000000, 9999999999999999)
        expire_date = datetime.now() + timedelta(hours=2)
        
        session['game_session'] = {
            'id': game_session_id,
            'quizz_id': id,
            'color': data[str(id)]['color'],
            'quizz_version_id': quizz_id,
            'expire_date': expire_date.strftime('%Y-%m-%d %H:%M:%S'),
            'date_start': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'questions': [
                {
                    'question': q['question'][3:] if q['question'][:3].isdigit() and q['question'][2] == '.' else q['question'],
                    'answers': q['answers'],
                    'correct': q['correct'],
                    'answered': False,
                    'selected_answers': []
                } for q in next(q for q in data[str(id)]['quizzes'] if q['id'] == quizz_id)['questions']
            ]
        }
        
        return redirect(url_for('play', game_session_id=game_session_id, question=0))
    except Exception as e:
        logging.error(e)
        flash('Une erreur est survenue', 'error')
        return redirect(url_for('index'))

@app.route('/play/<int:game_session_id>/<int:question>', methods=['GET', 'POST'])
def play(game_session_id, question):
    try:
        if 'game_session' not in session or int(session['game_session']['id']) != int(game_session_id):
            flash('Session invalide', 'error')
            return redirect(url_for('index'))
        elif datetime.now() > datetime.strptime(session['game_session']['expire_date'], '%Y-%m-%d %H:%M:%S'):
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
                
            if 'choice' not in request.form:
                answer = []
            else:
                if len(question_data[question_id]['correct']) == 1:
                    answer = [request.form['choice']]
                else:
                    answer = request.form.getlist('choice')
                
                question_data[question_id]['answered'] = True
                question_data[question_id]['selected_answers'] = answer
        
            session['game_session']['questions'] = question_data
            
            if end:
                return redirect(url_for('end', game_session_id=game_session_id))
            
            
            
        date_start = datetime.strptime(session['game_session']['date_start'], '%Y-%m-%d %H:%M:%S')
        
        print(date_start)
            
        return render_template('play.html', 
                               id=session['game_session']['id'], 
                               question=question, 
                               color=session['game_session']['color'], 
                               date_start=date_start,
                               question_data=question_data)
    except Exception as e:
        logging.error(e)
        flash('Une erreur est survenue', 'error')
        return redirect(url_for('index'))
    
@app.route('/play/<int:game_session_id>/end', methods=['GET'])
def end(game_session_id):
    try:
        if 'game_session' not in session or int(session['game_session']['id']) != int(game_session_id):
            flash('Session invalide',
                  'error')
            return redirect(url_for('index'))
        elif datetime.now() > datetime.strptime(session['game_session']['expire_date'], '%Y-%m-%d %H:%M:%S'):
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
            'date': datetime.now().strftime('%Y-%m-%d'),
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
            
        return redirect(url_for('attempt', quizz_id=quizz_id, quizz_version_id=quizz_version_id, attempt_id=attempt_id))
    except Exception as e:
        logging.error(e)
        flash('Une erreur est survenue', 'error')
        return redirect(url_for('index'))
    
@app.route('/quizz/<int:quizz_id>/attempt/<int:quizz_version_id>/<int:attempt_id>', methods=['GET'])
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
            
            print(questions_selected)
            print(quizz_version['questions'][i]['correct'])  
                        
            if set(quizz_version['questions'][i]['correct']) == set(questions_selected):
                index_of_right_answers.append(i)
        
        print(index_of_right_answers)
                
        data_to_show = {
            'id': quizz_id,
            'version_id': quizz_version_id,
            'title': quizz['title'],
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
        
        return render_template('attempt.html', data=data_to_show)
    except Exception as e:
        logging.error(e)
        return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    try:
        app.run(debug=True, port=port)
    except OSError as e:
        if 'Address already in use' in str(e):
            port += 1
            app.run(debug=True, port=port)
        else:
            raise e
