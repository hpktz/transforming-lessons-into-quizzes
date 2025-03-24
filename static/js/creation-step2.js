const quizz_notions = document.getElementById('quizz_notions');
const quizz_notions_container = document.getElementById('notions-container');
const return_button = document.getElementById('return_button');

const form = document.getElementById('quizz_form_stp2');

var notions_values = [];

quizz_notions.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        const value = quizz_notions.value;
        if (value !== '' && !notions_values.includes(value)) {
            const notion_container = document.createElement('div');
            notion_container.classList.add('notion-container');
            notion_container.id = "notion-" + value;
            
            const close_button = document.createElement('div');
            close_button.classList.add('close-button');
            close_button.addEventListener('click', function() {
                notion_container.remove();
                notions_values = notions_values.filter(function(notion) {
                    return notion !== value;
                });
            });
            
            const img_close_button = document.createElement('img');
            img_close_button.src = '/static/icons/icons8-close-60.png';
            img_close_button.alt = 'close';
            close_button.appendChild(img_close_button);

            notion_container.appendChild(close_button);

            const notion_text = document.createElement('div');
            notion_text.classList.add('text');
            notion_text.textContent = value;

            notion_container.appendChild(notion_text);

            quizz_notions_container.appendChild(notion_container);
            notions_values.push(value);
            quizz_notions.value = '';

        } else if (notions_values.includes(value)) {
            const notion_container = document.getElementById("notion-" + value);
            notion_container.classList.add('shake');
            setTimeout(function() {
                notion_container.classList.remove('shake');
            }, 500);

            quizz_notions.value = '';
        }
    }
});

form.addEventListener('submit', async function(event) {
    event.preventDefault();

    
});

const next_button = document.getElementById('next_button'); 
next_button.addEventListener('click', async function() {
    const main = document.getElementById('main');
    main.classList.add('to_go');

    const loader = document.getElementById('loader');
    loader.classList.remove('to_enter');

    const notions_input = document.getElementById('notions');
    notions_input.value = notions_values.join(',');

    try {
        const response = await fetch('/create/3', {
            method: 'POST',
            body: new FormData(form)
        });
        const data = await response.json();

        console.log(data);
        if (data.success) {
            window.location.href = '/?quizz=' + data.quizz_id;
        } else {
            main.classList.remove('to_go');
            loader.classList.add('to_enter');

            const message = document.getElementById('error-message');
            message.textContent = data.error;
        }
    } catch (error) {
        main.classList.remove('to_go');
        loader.classList.add('to_enter');

        const message = document.getElementById('error-message');
        message.textContent = 'Une erreur est survenue lors de la création du quizz';
    }
});

return_button.addEventListener('click', function() {
    window.location.href = '/create/1';
});

setTimeout(function() {
    const main = document.getElementById('main');
    main.classList.remove('to_enter');
}, 10);