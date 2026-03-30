const menuBtn = document.getElementById('menuBtn');
const menuDropdown = document.getElementById('menuDropdown');

if (menuBtn && menuDropdown) {
    menuBtn.onclick = function(e) {
        e.stopPropagation();
        menuDropdown.classList.toggle('show');
    };

    document.onclick = function(e) {
        if (!menuBtn.contains(e.target) && !menuDropdown.contains(e.target)) {
            menuDropdown.classList.remove('show');
        }
    };
}
