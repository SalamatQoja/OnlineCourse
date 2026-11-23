(function () {
    const panel = document.getElementById('progress-panel');
    if (!panel) return;

    const lessonId = panel.dataset.lessonId;
    const startUrl = panel.dataset.startUrl;
    const updateUrl = panel.dataset.updateUrl;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || '{{ csrf_token }}';

    const video = document.querySelector('video');
    const iframe = document.querySelector('iframe');   // для YouTube

    // --- 1) фиксируем старт, как только пользователь нажал play ---
    let started = false;

    async function markStart() {
        if (started) return;
        started = true;
        try {
            const res = await fetch(startUrl, {
                method: 'POST',
                headers: {'X-CSRFToken': csrfToken},
            });
            const data = await res.json();
            if (data.started_at) {
                document.getElementById('started-at').textContent =
                    new Date(data.started_at).toLocaleString();
            }
        } catch (e) {
            console.warn('start_lesson failed', e);
        }
    }

    // --- 2) считаем «реально просмотренное» время ---
    // delta копится только когда видео ИГРАЕТ.
    let lastTick = null;         // timestamp последнего тика
    let pendingDelta = 0;        // накопленное с прошлой отправки

    function tick() {
        const now = Date.now();
        if (lastTick && !document.hidden) {
            pendingDelta += Math.floor((now - lastTick) / 1000);
        }
        lastTick = now;
    }

    setInterval(tick, 1000);

    // --- 3) отправляем позицию + delta каждые 10 сек ---
    async function flush(extra = {}) {
        const position = video
            ? Math.floor(video.currentTime)
            : (extra.position ?? 0);

        const delta = pendingDelta;
        pendingDelta = 0;

        try {
            const res = await fetch(updateUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    position: position,
                    watched_delta: delta,
                }),
            });
            const data = await res.json();
            document.getElementById('progress-status').textContent =
                data.status;
            document.getElementById('position').textContent = data.position;
            document.getElementById('watched').textContent = data.watched;
        } catch (e) {
            console.warn('update_progress failed', e);
        }
    }

    setInterval(flush, 10000);

    // --- 4) отправляем при уходе со страницы ---
    window.addEventListener('beforeunload', () => {
        navigator.sendBeacon?.(
            updateUrl,
            new Blob([JSON.stringify({
                position: video ? Math.floor(video.currentTime) : 0,
                watched_delta: pendingDelta,
            })], {type: 'application/json'})
        );
    });

    // --- 5) старт просмотра ---
    if (video) {
        video.addEventListener('play', markStart);
        video.addEventListener('timeupdate', () => {
            lastTick = Date.now();
        });
    } else if (iframe) {
        // YouTube iframe — не отдаёт play-события без API.
        // Можно стартовать сразу, как только пользователь прокрутил.
        markStart();
    }
})();
