const quizz_containers = document.querySelectorAll('.quizz-container');

// Redirect to the quizz page when clicking on a quizz container

quizz_containers.forEach(function(quizz_container) {
    quizz_container.addEventListener('click', function() {
        const quizz_id = quizz_container.dataset.id;
        window.location.href = `/quizz/${quizz_id}`;
    });
});
