document.addEventListener('click', function (e) {
    var btn = e.target.closest('.toggle-btn');
    if (!btn) return;

    var body = document.getElementById(btn.getAttribute('aria-controls'));
    if (!body) return;

    var willOpen = body.hasAttribute('hidden');
    body.toggleAttribute('hidden', !willOpen);
    btn.setAttribute('aria-expanded', willOpen);
    btn.classList.toggle('is-open', willOpen);
    btn.querySelector('.toggle-btn__text').textContent = willOpen ? btn.dataset.hide : btn.dataset.show;
});