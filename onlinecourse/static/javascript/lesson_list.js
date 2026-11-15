(function () {
    var app = document.getElementById('lessonApp');
    if (!app) return;

    var modules = Array.prototype.slice.call(app.querySelectorAll('.lp-module'));
    var courses = Array.prototype.slice.call(app.querySelectorAll('.lp-course'));
    var noResults = document.getElementById('noResults');

    function setOpen(module, open) {
        var btn = module.querySelector('.lp-module__toggle');
        var body = module.querySelector('.lp-module__body');
        body.toggleAttribute('hidden', !open);
        btn.setAttribute('aria-expanded', open);
        module.classList.toggle('is-open', open);
    }

    app.addEventListener('click', function (e) {
        var btn = e.target.closest('.lp-module__toggle');
        if (!btn) return;
        var module = btn.closest('.lp-module');
        var isHidden = module.querySelector('.lp-module__body').hasAttribute('hidden');
        setOpen(module, isHidden);
    });

    document.getElementById('expandAll').addEventListener('click', function () {
        modules.forEach(function (m) {
            if (!m.hidden) setOpen(m, true);
        });
    });
    document.getElementById('collapseAll').addEventListener('click', function () {
        modules.forEach(function (m) {
            setOpen(m, false);
        });
    });

    var select = document.getElementById('courseSelect');
    if (select) {
        select.addEventListener('change', function () {
            select.form.submit();
        });
    }
    
    var input = document.getElementById('lessonSearch');
    if (input) {
        input.addEventListener('input', function () {
            var q = input.value.trim().toLowerCase();
            var anyVisible = false;

            modules.forEach(function (module) {
                var lessons = module.querySelectorAll('.lp-lesson');
                var matches = 0;

                lessons.forEach(function (li) {
                    var show = !q || li.dataset.name.indexOf(q) !== -1;
                    li.hidden = !show;
                    if (show) matches++;
                });

                var visible = !q || matches > 0;
                module.hidden = !visible;
                if (q && matches > 0) setOpen(module, true);
                if (visible) anyVisible = true;
            });

            courses.forEach(function (course) {
                var hasVisible = course.querySelector('.lp-module:not([hidden])');
                course.hidden = !!q && !hasVisible;
            });

            if (noResults) noResults.hidden = !q || anyVisible;
        });
    }
})();