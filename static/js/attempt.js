const return_button = document.getElementById('return_button');
const progress_items = document.querySelectorAll('.progress_item');
const try_again_button = document.getElementById('try_again_button');
const explanation_sources = document.querySelectorAll('.explanation_source');

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

explanation_sources.forEach((source) => {
    source.addEventListener('click', () => {
        console.log(source);
        const page = source.dataset.page;
        const sourceText = source.dataset.source;
        const doc_url = source.dataset.doc;

        // Navigate to the doc url and to the page, highlighting the source in the pdf viewer
        window.open(`${doc_url}#page=${page}&source=${encodeURIComponent(sourceText)}`, '_blank');
    });
});