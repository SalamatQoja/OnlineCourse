(function () {
    var input = document.getElementById('courseSearch');
    if (!input) return;

    var items = document.querySelectorAll('[data-course-name]');
    var empty = document.getElementById('courseNoResults');

    input.addEventListener('input', function () {
        var q = input.value.trim().toLowerCase();
        var shown = 0;

        items.forEach(function (el) {
            var ok = !q || el.dataset.courseName.indexOf(q) !== -1;
            el.hidden = !ok;
            if (ok) shown++;
        });

        if (empty) empty.hidden = !q || shown > 0;
    });
})();