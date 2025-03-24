const progress_item = document.querySelectorAll('.progress_item');
const form = document.getElementById('form');

const previous_button = document.getElementById('previous_button');
const next_button = document.getElementById('next_button');
const end_button = document.getElementById('end_button');
const main_end_button = document.getElementById('main_end_button');

progress_item.forEach(function(item) {
    item.addEventListener('click', function() {
        const id = item.dataset.id;
        const next_quest = item.dataset.quest;

        form.action = `/play/${id}/${next_quest}`;
        form.submit();
    });
});

if (previous_button) {
    previous_button.addEventListener('click', function() {
        const id = previous_button.dataset.id;
        const previous_quest = previous_button.dataset.next_quest;
        form.action = `/play/${id}/${previous_quest}`;
        form.submit();
    });
}

if (next_button) {
    next_button.addEventListener('click', function() {
        const id = next_button.dataset.id;
        const next_quest = next_button.dataset.next_quest;
        form.action = `/play/${id}/${next_quest}`;
        form.submit();
    });
}

if (end_button) {
    end_button.addEventListener('click', function() {
        const id = end_button.dataset.id;
        const next_quest = end_button.dataset.next_quest;

        form.action = `/play/${id}/${next_quest}`;
        const end_input = document.getElementById('end');
        end_input.value = '1';
        form.submit();
    });
}

if (main_end_button) {
    main_end_button.addEventListener('click', function() {
        const id = main_end_button.dataset.id;
        const next_quest = main_end_button.dataset.next_quest;

        form.action = `/play/${id}/${next_quest}`;
        const end_input = document.getElementById('end');
        end_input.value = '1';
        form.submit();
    });
}