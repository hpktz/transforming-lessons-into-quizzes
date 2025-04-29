const course_pdf = document.getElementById('course_pdf');
const cours_pdf_label = document.getElementById('course_pdf_label');

const quizz_pdf = document.getElementById('quizz_pdf');
const quizz_pdf_label = document.getElementById('quizz_pdf_label');

const form = document.getElementById('extraction_form_stp1');

// Reusable function to handle file change
function handleFileChange(fileInput, fileLabel) {
    const file = fileInput.files[0];
    if (!file) return;
    
    fileLabel.innerHTML = '';

    const upload_infos = document.createElement('div');
    upload_infos.classList.add('upload_infos');

    const doc_preview = document.createElement('div');
    doc_preview.classList.add('doc_preview');

    const imgPreview = document.createElement('img');
    imgPreview.src = '/static/icons/docs.png';
    doc_preview.appendChild(imgPreview);

    const doc_infos = document.createElement('div');
    doc_infos.classList.add('doc_infos');

    // File name
    const doc_name = document.createElement('div');
    doc_name.classList.add('doc_name');
    doc_name.textContent = file.name;
    doc_infos.appendChild(doc_name);

    // File modification date
    const fileDate = new Date(file.lastModified);
    const doc_date = document.createElement('div');
    doc_date.classList.add('doc_date');
    doc_date.textContent = fileDate.toLocaleDateString();
    doc_infos.appendChild(doc_date);

    upload_infos.appendChild(doc_preview);
    upload_infos.appendChild(doc_infos);
    fileLabel.appendChild(upload_infos);
}

// Add event listeners using the shared function
course_pdf.addEventListener('change', () => handleFileChange(course_pdf, cours_pdf_label));
quizz_pdf.addEventListener('change', () => handleFileChange(quizz_pdf, quizz_pdf_label));


form.addEventListener('submit', async function(event) {
    event.preventDefault();
});

const next_button = document.getElementById('next_button'); 
next_button.addEventListener('click', async function() {
    const main = document.getElementById('main');
    main.classList.add('to_go');

    const loader = document.getElementById('loader');
    loader.classList.remove('to_enter');

    try {
        const response = await fetch('/extract/2', {
            method: 'POST',
            body: new FormData(form)
        });
        const data = await response.json();

        console.log(data);
        if (data.success) {
            window.location.href = '/folder/' + data.folder_id + '?quizz=' + data.quizz_id;
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
    window.location.href = '/';
});