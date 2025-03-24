const course_pdf = document.getElementById('course_pdf');
const cours_pdf_label = document.getElementById('course_pdf_label');
const return_button = document.getElementById('return_button');

const form = document.getElementById('quizz_form_stp1');

course_pdf.addEventListener('change', function() {
    const file = course_pdf.files[0];
    if (file) {
        cours_pdf_label.innerHTML = '';

        const upload_infos = document.createElement('div');
        upload_infos.classList.add('upload_infos');

        const doc_preview = document.createElement('div');
        doc_preview.classList.add('doc_preview');

        const imgPreview = document.createElement('img');
        imgPreview.src = '/static/icons/docs.png';
        doc_preview.appendChild(imgPreview);

        upload_infos.appendChild(doc_preview);


        const doc_infos = document.createElement('div');
        doc_infos.classList.add('doc_infos');

        // Récupérer le nom du fichier
        const fileName = file.name;
        const doc_name = document.createElement('div');
        doc_name.classList.add('doc_name');
        doc_name.textContent = fileName;

        doc_infos.appendChild(doc_name);

        // Récupérer la date de modification du fichier
        const fileDate = new Date(file.lastModified);
        const formattedDate = fileDate.toLocaleDateString();
        const doc_date = document.createElement('div');
        doc_date.classList.add('doc_date');
        doc_date.textContent = formattedDate;

        doc_infos.appendChild(doc_date);

        upload_infos.appendChild(doc_infos);

        cours_pdf_label.appendChild(upload_infos);
    }
});


form.addEventListener('submit', function(event) {
    event.preventDefault();

    const main = document.getElementById('main');
    main.classList.add('to_go');

    setInterval(function() {
        event.target.submit();
    }, 600);
});

return_button.addEventListener('click', function() {
    window.location.href = '/';
});