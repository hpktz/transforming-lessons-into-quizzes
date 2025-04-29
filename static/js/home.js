const quizz_containers = document.querySelectorAll('.quizz-container');
const delete_buttons = document.querySelectorAll('.delete_container');

const create_button = document.querySelector('#create-button');
const return_button = document.querySelector('#return_button');
const create_quizz = document.querySelector('#create_quizz');
const create_folder = document.querySelector('#create_folder');
const return_button_folder = document.querySelector('#return_button_folder');

const choices_container = document.querySelectorAll('.choice-container');

const folder_container = document.querySelectorAll('.folder-container');

const path_item = document.querySelectorAll('.path-item');

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

delete_buttons.forEach(function(delete_button) {
    delete_button.addEventListener('click', function() {
        const quizz_id = delete_button.dataset.id;

        window.location.href = `/delete/${quizz_id}`;
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