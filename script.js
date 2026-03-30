const menuBtn = document.getElementById('menuBtn');
const menuDropdown = document.getElementById('menuDropdown');

// Ouvrir/fermer le menu
menuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    menuDropdown.classList.toggle('show');
});

// Fermer le menu si on clique ailleurs
document.addEventListener('click', () => {
    menuDropdown.classList.remove('show');
});

// Fermer le menu si on clique sur un lien
document.querySelectorAll('.menu-dropdown a').forEach(link => {
    link.addEventListener('click', () => {
        menuDropdown.classList.remove('show');
    });
});
