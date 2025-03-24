const return_button = document.getElementById('return_button');
const progress_items = document.querySelectorAll('.progress_item');
const try_again_button = document.getElementById('try_again_button');


return_button.addEventListener('click', () => {
    const quizz_id = return_button.dataset.quizz_id;
    window.location.href = `/quizz/${quizz_id}`;
});

progress_items.forEach((item) => {
    item.addEventListener('click', () => {
        const quest_nb = item.dataset.quest;
        const id_of_quest = 'question_' + quest_nb;

        console.log(id_of_quest);
        // Go to the question section
        window.location.href = `#${id_of_quest}`;
    });
});

try_again_button.addEventListener('click', () => {
    const id = try_again_button.dataset.id;
    const quizz_id = try_again_button.dataset.quizz_id;
    window.location.href = `/quizz/${id}/play/${quizz_id}`;
});