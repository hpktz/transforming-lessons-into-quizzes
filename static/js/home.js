const quizz_containers = document.querySelectorAll('.quizz-container');
const option_quizz_container = document.querySelectorAll('.option_container');

const delete_quizz = document.querySelector('#delete_quizz');
const modify_quizz = document.querySelector('#modify_quizz');
const modify_quizz_close = document.querySelector('#return_button_modify_quizz');

const create_button = document.querySelector('#create-button');
const return_button = document.querySelector('#return_button');
const create_quizz = document.querySelector('#create_quizz');
const create_folder = document.querySelector('#create_folder');
const return_button_folder = document.querySelector('#return_button_folder');

const choices_container = document.querySelectorAll('.choice-container');

const folder_container = document.querySelectorAll('.folder-container');

const path_item = document.querySelectorAll('.path-item');

const update_button = document.querySelector('#update-button');

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

quizz_containers.forEach(function(quizz_container) {
    // Drag and drop functionality
    quizz_container.addEventListener('dragstart', function(event) {
        const quizz_id = quizz_container.dataset.id;
        event.dataTransfer.setData('text/plain', quizz_id);

        // Set the drag image to the container itself
        const rect = quizz_container.getBoundingClientRect();
        const offsetX = event.clientX - rect.left;
        const offsetY = event.clientY - rect.top;
        event.dataTransfer.setDragImage(quizz_container, offsetX, offsetY);
    });
});

option_quizz_container.forEach(function(option_container) {
    option_container.addEventListener('click', function(event) {
        event.stopPropagation(); // Prevent the click from propagating to the quizz container
        const option_menu = document.querySelector('.choice-quizz-container');
        option_menu.style.display = "block";
        option_menu.style.left = `${event.clientX}px`;
        option_menu.style.top = `${event.clientY}px`;

        document.getElementById('delete_quizz').dataset.id = option_container.dataset.id;
        document.getElementById('modify_quizz').dataset.id = option_container.dataset.id;

        setTimeout(() => {
            const body = document.querySelector('body');
            body.addEventListener('click', function() {
                option_menu.style.display = "none";
            }, { once: true });
        }, 10);
    });
});

delete_quizz.addEventListener('click', function(event) {
    window.location.href = `/delete/${delete_quizz.dataset.id}`;
});

modify_quizz.addEventListener('click', async function(event) {
    event.preventDefault();
    const modify_popup = document.querySelector('.modify-quizz-popup');
    modify_popup.classList.add('active');

    const main = document.querySelector('main');
    main.style.pointerEvents = 'none';

    const quizz_id = modify_quizz.dataset.id;
    try {
        const response = await fetch(`/get_quizz/${quizz_id}`);
        const quizz_data = await response.json();

        const form = modify_popup.querySelector('form');
        form.action = `/modify/${quizz_id}`;

        const text_field = document.getElementById('quizz_name_modify');
        const emoji_field = document.getElementById('quizz_emoji_modify');
        const color_inputs = document.getElementsByName('quizz_color');

        text_field.value = quizz_data.title;
        emoji_field.value = quizz_data.emoji;
        color_inputs.forEach(function(input) {
            console.log(input.value, quizz_data.color);
            if (input.value === quizz_data.color) {
                input.checked = true;
            }
        });
        
    } catch (error) {
        console.error('Error fetching quizz data:', error);
        modify_popup.classList.remove('active');
        main.style.pointerEvents = 'auto';
        return;
    }
});

modify_quizz_close.addEventListener('click', function(event) {
    const modify_popup = document.querySelector('.modify-quizz-popup');
    modify_popup.classList.remove('active');

    // Unselect all the fields and reset the values
    modify_popup.querySelector('form').reset();

    const main = document.querySelector('main');
    main.style.pointerEvents = 'auto';
});

folder_container.forEach(function(folder) {
    folder.addEventListener('dragover', function(event) {
        event.preventDefault();
        folder.classList.add('drag-over'); // Add a visual indicator for drag-over
    });

    folder.addEventListener('dragleave', function(event) {
        folder.classList.remove('drag-over'); // Remove the visual indicator when dragging leaves
    });

    folder.addEventListener('drop', function(event) {
        event.preventDefault();
        folder.classList.remove('drag-over'); // Ensure the visual indicator is removed on drop
        const quizz_id = event.dataTransfer.getData('text/plain');
        const folder_id = folder.dataset.id;

        // Send a request to move the quizz to the folder
        fetch(`/move_quizz/${quizz_id}/${folder_id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ quizz_id, folder_id })
        })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                console.error('Error moving quizz:', response.statusText);
            }
        })
        .catch(error => {
            console.error('Network error:', error);
        });
    });
});

path_item.forEach(function(path) {  
    path.addEventListener('click', function(event) {
        event.stopPropagation();
        const path_id = path.dataset.folder_id;
        window.location.href = `/folder/${path_id}`;
    })
    path.addEventListener('dragover', function(event) {
        event.preventDefault();
        path.classList.add('drag-over'); // Add a visual indicator for drag-over
    });
    path.addEventListener('dragleave', function(event) {
        path.classList.remove('drag-over'); // Remove the visual indicator when dragging leaves
    });
    path.addEventListener('drop', function(event) {
        event.preventDefault();
        path.classList.remove('drag-over'); // Ensure the visual indicator is removed on drop
        const quizz_id = event.dataTransfer.getData('text/plain');
        const folder_id = path.dataset.folder_id;

        // Send a request to move the quizz to the folder
        fetch(`/move_quizz/${quizz_id}/${folder_id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ quizz_id, folder_id })
        })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                console.error('Error moving quizz:', response.statusText);
            }
        })
        .catch(error => {
            console.error('Network error:', error);
        });
    });
});

create_button.addEventListener('click', function(event) {
    event.preventDefault();
    const create_popup = document.querySelector('.choice-type-container');
    create_popup.style.display = 'block';
    create_popup.style.left = `${event.clientX}px`;
    create_popup.style.top = `${event.clientY}px`;

    setTimeout(() => {
        const body = document.querySelector('body');
        body.addEventListener('click', function() {
            create_popup.style.left = `-50%`;
        }, { once: true });
    }, 10);
});

document.querySelector(".main-container").addEventListener('contextmenu', function(event) {
    event.preventDefault();
    const create_popup = document.querySelector('.choice-type-container');
    create_popup.style.display = 'block';
    create_popup.style.left = `${event.clientX}px`;
    create_popup.style.top = `${event.clientY}px`;

    setTimeout(() => {
        const body = document.querySelector('body');
        body.addEventListener('click', function() {
            create_popup.style.left = `-50%`;
        }, { once: true });
    }, 10);
});

create_quizz.addEventListener('click', function(event) {
    event.preventDefault();
    const create_popup = document.querySelector('.create-popup');
    create_popup.classList.add('active');

    const main = document.querySelector('main');
    main.style.pointerEvents = 'none';
});

return_button.addEventListener('click', function(event) {
    event.preventDefault();
    const create_popup = document.querySelector('.create-popup');
    create_popup.classList.remove('active');

    const main = document.querySelector('main');
    main.style.pointerEvents = 'auto';
});

choices_container.forEach(function(choices) {
    choices.addEventListener('click', function(event) {
        event.stopPropagation();
        
        console.log(choices);

        const url = choices.dataset.url;
        window.location.href = url;
    });
});

document.querySelectorAll('.folder, .subfolder').forEach(element => {
    let level = 0;
    let parent = element;
    if ((parent = parent.parentNode) && parent.classList.contains('subfolder') || parent.classList.contains('folder')) {
        level++;
    }
    element.style.marginLeft = `${level * 20}px`;
});

document.addEventListener('DOMContentLoaded', function () {
    const toggleButtons = document.querySelectorAll('.toggle-button');

    toggleButtons.forEach(button => {
        button.addEventListener('click', function () {
            const subfolders = Array.from(button.closest('.content').parentNode.children)
                .filter(child => child.classList.contains('subfolder'));
            subfolders.forEach(subfolder => {
                if (subfolder.style.display === 'none' || subfolder.style.display === '') {
                    subfolder.style.display = 'block';
                    button.textContent = '▲'; // Change l'icône pour indiquer que les dossiers sont ouverts
                } else {
                    subfolder.style.display = 'none';
                    button.textContent = '▼'; // Change l'icône pour indiquer que les dossiers sont fermés
                }
            });
        });
    });
});

create_folder.addEventListener('click', function(event) {
    event.preventDefault();
    const create_popup = document.querySelector('.create-folder-popup');
    create_popup.classList.add('active');

    const main = document.querySelector('main');
    main.style.pointerEvents = 'none';
});

return_button_folder.addEventListener('click', function(event) {
    event.preventDefault();
    const create_popup = document.querySelector('.create-folder-popup');
    create_popup.classList.remove('active');

    const main = document.querySelector('main');
    main.style.pointerEvents = 'auto';
});

folder_container.forEach(function(folder) {
    folder.addEventListener('click', function(event) {
        event.stopPropagation();
        const folder_id = folder.dataset.id;
        window.location.href = `/folder/${folder_id}`;
    });
});

// Redirect to folder page when clicking on a folder container
document.querySelectorAll('.content').forEach(function(content) {
    content.addEventListener('click', function(event) {
        event.stopPropagation();
        const toggleButton = event.target.closest('.toggle-button');
        if (toggleButton) {
            return; 
        }


        const folder_id = content.dataset.id;
        window.location.href = `/folder/${folder_id}`;
    });
});

update_button.addEventListener('click', function(event) {
    window.location.href = '/update_report';
});