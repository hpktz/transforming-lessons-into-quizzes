const preview_container = document.getElementById('preview_container');
const generate_button = document.getElementById('generate_button');
const launch_buttons = document.querySelectorAll('.quizz_start_button');
const show_attempts_buttons = document.querySelectorAll('.quizz_show_button');
const return_button = document.getElementById('return_button');
const attempt_check_buttons = document.querySelectorAll('.attempt_check_button');


preview_container.addEventListener('click', function() {
    const pdf_url = preview_container.dataset.url;
    window.location.href = `${pdf_url}`;
});


generate_button.addEventListener('click', async function() {
    generate_button.innerHTML = '<div class="loader"></div>';
    generate_button.disabled = true;
    generate_button.classList.add('active');

    const quizz_id = generate_button.dataset.id;
    try {
        const response = await fetch(`/quizz/${quizz_id}/generate`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            window.location.href = `/quizz/${quizz_id}?generated=true#generate_button`;
        } else {
            generate_button.classList.remove('active');
            generate_button.classList.add('error');
            generate_button.innerHTML = 'Erreur dans la génération';
            setTimeout(function() {
                generate_button.classList.remove('error');
                generate_button.innerHTML = 'Générer un autre quizz';
                generate_button.disabled = false;
            }, 2000);
        }
    } catch (error) {
        generate_button.classList.remove('active');
        generate_button.classList.add('error');
        generate_button.innerHTML = 'Erreur de génération';
        setTimeout(function() {
            generate_button.classList.remove('error');
            generate_button.innerHTML = 'Générer un autre quizz';
            generate_button.disabled = false;
        }, 2000);
    }
});

launch_buttons.forEach(function(launch_button) {
    launch_button.addEventListener('click', function() {
        const id = launch_button.dataset.id;
        const quizz_id = launch_button.dataset.quizz_id;
        window.location.href = `/quizz/${id}/play/${quizz_id}`;
    });
});

show_attempts_buttons.forEach(function(show_attempts_button) {
    show_attempts_button.addEventListener('click', function() {
        const quizz_id = show_attempts_button.dataset.quizz_id;
        const quizz_main_container = document.getElementById(`quizz_container_${quizz_id}`);

        if (show_attempts_button.classList.contains('active')) {
            show_attempts_button.classList.remove('active');

            quizz_main_container.querySelector('.quizz_attempts').classList.remove('active');
        } else {
            show_attempts_button.classList.add('active');
            quizz_main_container.querySelector('.quizz_attempts').classList.add('active');
        }
        
    });
});

return_button.addEventListener('click', function() {
    window.location.href = '/';
});

attempt_check_buttons.forEach(function(attempt_check_button) {
    attempt_check_button.addEventListener('click', function() {
        const id = attempt_check_button.dataset.id;
        const quizz_id = attempt_check_button.dataset.quizz_id;
        const attempt_id = attempt_check_button.dataset.attempt_id;
        window.location.href = `/quizz/${id}/attempt/${quizz_id}/${attempt_id}`;
    });
});