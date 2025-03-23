const preview_container = document.getElementById('preview_container');
const generate_button = document.getElementById('generate_button');


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
        generate_button.innerHTML = 'Erreur dans la génération';
        setTimeout(function() {
            generate_button.classList.remove('error');
            generate_button.innerHTML = 'Générer un autre quizz';
            generate_button.disabled = false;
        }, 2000);
    }
   

});