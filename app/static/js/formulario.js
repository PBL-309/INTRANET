document.addEventListener('DOMContentLoaded', function () {
    const modal = new bootstrap.Modal(document.getElementById('anonimoModal'));
    const aceptarBtn = document.getElementById('aceptarAnonimato');
    const formularioContainer = document.getElementById('formularioContainer');
    modal.show();
    aceptarBtn.addEventListener('click', () => {
        modal.hide();
        formularioContainer.style.display = 'block';
    });
});
