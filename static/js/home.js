const quizz_containers = document.querySelectorAll('.quizz-container');
const delete_buttons = document.querySelectorAll('.delete_container');

// Redirect to the quizz page when clicking on a quizz container

quizz_containers.forEach(function(quizz_container) {
    quizz_container.addEventListener('click', function() {
        const rect = quizz_container.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const clickY = event.clientY - rect.top;

        if (clickX < rect.width - 50 || clickY > 50) {
            const quizz_id = quizz_container.dataset.id;
            window.location.href = `/quizz/${quizz_id}`;
        }
    });
});

delete_buttons.forEach(function(delete_button) {
    delete_button.addEventListener('click', function() {
        const quizz_id = delete_button.dataset.id;

        window.location.href = `/delete/${quizz_id}`;
    });
});