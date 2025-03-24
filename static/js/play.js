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

// Ajoutez ce code à votre fichier play.js existant
document.addEventListener('DOMContentLoaded', function() {
    // Récupération de l'élément chronomètre
    const chronometreElement = document.querySelector('.chronometre');
    
    if (!chronometreElement) return;
    
    // Récupération de la date de départ depuis l'attribut data-start
    const dateStart = chronometreElement.getAttribute('data-start');
    
    // Conversion en objet Date JavaScript
    const startDate = new Date(dateStart);
    
    // Vérification de la validité de la date
    if (isNaN(startDate.getTime())) {
        console.error('Format de date invalide:', dateStart);
        return;
    }
    
    // Éléments d'affichage
    const minutesElement = document.getElementById('minutes');
    const secondsElement = document.getElementById('seconds');
    const millisecondsElement = document.getElementById('milliseconds');
    
    // Fonction pour mettre à jour le chronomètre
    function updateChronometre() {
        // Obtenir l'heure actuelle
        const currentDate = new Date();
        
        // Calculer la différence en millisecondes
        const elapsedTime = currentDate - startDate;
        
        // Convertir en minutes, secondes et millisecondes
        const minutes = Math.floor(elapsedTime / 60000);
        const seconds = Math.floor((elapsedTime % 60000) / 1000);
        const milliseconds = Math.floor((elapsedTime % 1000) / 10); // Centièmes de seconde
        
        // Mettre à jour l'affichage avec formatage à deux chiffres
        minutesElement.textContent = minutes.toString().padStart(2, '0');
        secondsElement.textContent = seconds.toString().padStart(2, '0');
        millisecondsElement.textContent = milliseconds.toString().padStart(2, '0');
        
        // Continuer indéfiniment
        requestAnimationFrame(updateChronometre);
    }
    
    // Démarrer le chronomètre
    updateChronometre();
});