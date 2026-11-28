/**
 * Motion: the detection-box counter, scroll reveals, the stats count-up and
 * the hero parallax.
 *
 * theme.js decides whether motion happens at all — it adds .motion-ready to
 * <html> unless the visitor asked for reduced motion — and withdraws the
 * flag if this file has not run within three seconds. This file only adds
 * behaviour on top: with it missing, every element is already visible.
 */
(function () {
    'use strict';

    window.portfolioMotion = true;

    // Arriving after theme.js gave up (slow network) counts as "no motion".
    if (!document.documentElement.classList.contains('motion-ready')) {
        return;
    }

    var motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    var active = true;
    var cleanups = [];

    function disableMotion() {
        if (!motion.matches || !active) {
            return;
        }
        active = false;
        document.documentElement.classList.remove('motion-ready');
        cleanups.forEach(function (cleanup) { cleanup(); });
        cleanups = [];
    }

    motion.addEventListener('change', disableMotion);
    disableMotion();

    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    function format(value, decimals, pad) {
        var text = value.toFixed(decimals);
        return pad && value < 9.5 ? '0' + text : text;
    }

    function countTo(element, target, decimals, duration, pad) {
        var start = null;
        var frameId;
        function frame(timestamp) {
            if (!active) { return; }
            if (start === null) {
                start = timestamp;
            }
            var progress = Math.min((timestamp - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = format(target * eased, decimals, pad);
            if (progress < 1) {
                frameId = window.requestAnimationFrame(frame);
            }
        }
        frameId = window.requestAnimationFrame(frame);
        cleanups.push(function () {
            window.cancelAnimationFrame(frameId);
            element.textContent = format(target, decimals, pad);
        });
    }

    /* A short, original code and title reveal; the canvas never intercepts input. */
    function initCinematic() {
        var scene = document.querySelector('.hero-cinematic');
        var canvas = document.querySelector('.hero-code-canvas');
        var title = document.querySelector('.hero-cinematic-title');
        var zoomLetter = document.querySelector('.hero-cinematic-v');
        if (!scene || !canvas || !title || !zoomLetter || motion.matches || document.hidden) {
            return;
        }
        var context = canvas.getContext('2d');
        if (!context) {
            return;
        }

        var letters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ+-/';
        var colors = getComputedStyle(document.documentElement);
        var red = colors.getPropertyValue('--color-stage-accent').trim();
        var light = colors.getPropertyValue('--color-on-stage').trim();
        var width, height, frameId, started, fallbackTimer;
        var duration = 7000;
        var streams = [];

        function makeStreams(count) {
            streams = [];
            for (var i = 0; i < count; i += 1) {
                var length = 6 + Math.floor(Math.random() * 13);
                var glyphs = [];
                for (var j = 0; j < length; j += 1) {
                    glyphs.push(Math.floor(Math.random() * letters.length));
                }
                streams.push({
                    x: (i + Math.random() * 0.6) / count,
                    offset: Math.random(),
                    speed: 0.25 + Math.random() * 0.35,
                    length: length,
                    glyphs: glyphs
                });
            }
        }

        function resize() {
            var ratio = Math.min(window.devicePixelRatio || 1, 1.5);
            width = scene.clientWidth;
            height = scene.clientHeight;
            canvas.width = Math.max(1, Math.round(width * ratio));
            canvas.height = Math.max(1, Math.round(height * ratio));
            context.setTransform(ratio, 0, 0, ratio, 0, 0);
            var count = Math.max(20, Math.min(96, Math.floor(width / 15)));
            if (streams.length !== count) { makeStreams(count); }
            var origin = zoomLetter.offsetLeft + zoomLetter.offsetWidth / 2;
            title.style.setProperty('--zoom-origin-x', origin + 'px');
            title.style.setProperty('--zoom-shift-x', (title.offsetWidth / 2 - origin) + 'px');
        }

        function stop() {
            window.cancelAnimationFrame(frameId);
            scene.classList.remove('is-playing');
            document.documentElement.classList.remove('cinematic-active');
            window.clearTimeout(fallbackTimer);
            window.removeEventListener('resize', resize);
            window.removeEventListener('pointerdown', stop);
            window.removeEventListener('keydown', stop);
            window.removeEventListener('scroll', stop);
            document.removeEventListener('visibilitychange', onVisibilityChange);
            motion.removeEventListener('change', onMotionChange);
        }

        function onVisibilityChange() {
            if (document.hidden) { stop(); }
        }

        function onMotionChange() {
            if (motion.matches) { stop(); }
        }

        function draw(timestamp) {
            if (started === undefined) { started = timestamp; }
            var elapsed = timestamp - started;
            if (elapsed >= duration) {
                stop();
                return;
            }
            if (elapsed >= duration * 0.7) {
                window.clearTimeout(fallbackTimer);
                fallbackTimer = window.setTimeout(stop, duration - elapsed);
                return;
            }
            context.clearRect(0, 0, width, height);
            var time = elapsed / 1000;
            var glyphStep = Math.floor(elapsed / 700);
            var size = Math.max(11, Math.min(16, width / 60));
            var spacing = size * 1.35;

            context.textAlign = 'center';
            context.textBaseline = 'middle';
            context.font = '500 ' + size + 'px monospace';
            streams.forEach(function (stream) {
                var head = ((stream.offset + time * stream.speed) % 1.5) * (height + stream.length * spacing) - stream.length * spacing;
                for (var n = 0; n < stream.length; n += 1) {
                    var y = head - n * spacing;
                    if (y < 0 || y > height) { continue; }
                    context.fillStyle = n === 0 ? light : red;
                    context.globalAlpha = 0.12 + 0.78 * (1 - n / stream.length);
                    if (n === 0) {
                        context.shadowColor = red;
                        context.shadowBlur = 10;
                    }
                    var glyph = stream.glyphs[n];
                    if (n === (glyphStep + stream.glyphs[0]) % stream.length) {
                        glyph = (glyph + glyphStep) % letters.length;
                    }
                    context.fillText(letters[glyph], stream.x * width, y);
                    context.shadowBlur = 0;
                }
            });

            context.globalAlpha = 1;
            frameId = window.requestAnimationFrame(draw);
        }

        scene.classList.add('is-playing');
        document.documentElement.classList.add('cinematic-active');
        resize();
        window.addEventListener('resize', resize);
        window.addEventListener('pointerdown', stop, { once: true });
        window.addEventListener('keydown', stop, { once: true });
        window.addEventListener('scroll', stop, { once: true, passive: true });
        document.addEventListener('visibilitychange', onVisibilityChange);
        motion.addEventListener('change', onMotionChange);
        fallbackTimer = window.setTimeout(stop, duration + 200);
        if (document.fonts) {
            document.fonts.ready.then(function () {
                if (scene.classList.contains('is-playing')) { resize(); }
            });
        }
        frameId = window.requestAnimationFrame(draw);
        cleanups.push(stop);
    }

    /* --- Detection label: the confidence counts up as the box lands ------ */
    function initDetection() {
        var score = document.querySelector('.hero-detect-score');
        if (!score) {
            return;
        }
        var target = parseFloat(score.getAttribute('data-score')) || 0;
        score.textContent = format(0, 2, false);
        // Matches the label's fade-in delay in motion.css.
        var timer = window.setTimeout(function () {
            countTo(score, target, 2, 600, false);
        }, 1450);
        cleanups.push(function () {
            window.clearTimeout(timer);
            score.textContent = format(target, 2, false);
        });
    }

    /* --- Stats: count up the first time each one is on screen ------------- */
    function initCountUp() {
        var stats = Array.prototype.slice.call(document.querySelectorAll('[data-count]'));
        if (!stats.length || !('IntersectionObserver' in window)) {
            return;
        }
        var observer = new IntersectionObserver(function (entries) {
            if (!active) { return; }
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) {
                    return;
                }
                var target = parseInt(entry.target.getAttribute('data-count'), 10) || 0;
                countTo(entry.target, target, 0, 1200, true);
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.6 });
        stats.forEach(function (stat) {
            stat.textContent = format(0, 0, true);
            observer.observe(stat);
        });
        cleanups.push(function () {
            observer.disconnect();
            stats.forEach(function (stat) {
                stat.textContent = format(parseInt(stat.getAttribute('data-count'), 10) || 0, 0, true);
            });
        });
    }

    /* --- Scroll reveals ---------------------------------------------------
       [data-reveal] elements start hidden (motion.css) and are revealed as
       they enter the viewport, staggered among their revealing siblings. */
    function initReveals() {
        var items = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));
        if (!items.length) {
            return;
        }

        if (!('IntersectionObserver' in window)) {
            items.forEach(function (item) {
                item.classList.add('is-revealed');
            });
            return;
        }
        var observer = new IntersectionObserver(function (entries) {
            if (!active) { return; }
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) {
                    return;
                }
                entry.target.classList.add('is-revealed');
                observer.unobserve(entry.target);
            });
        }, { rootMargin: '0px 0px -8% 0px', threshold: 0 });

        items.forEach(function (item) {
            var index = 0;
            var sibling = item.previousElementSibling;
            while (sibling) {
                if (sibling.hasAttribute('data-reveal')) {
                    index += 1;
                }
                sibling = sibling.previousElementSibling;
            }
            item.style.setProperty('--reveal-delay', Math.min(index, 6) * 90 + 'ms');
            observer.observe(item);
        });
        cleanups.push(function () { observer.disconnect(); });
    }

    function initMotionLines() {
        var lines = document.querySelectorAll('.timeline');
        if (!('IntersectionObserver' in window)) {
            return;
        }
        var observer = new IntersectionObserver(function (entries) {
            if (!active) { return; }
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-drawing');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0 });
        lines.forEach(function (line) { observer.observe(line); });
        cleanups.push(function () { observer.disconnect(); });
    }

    /* --- Hero parallax ----------------------------------------------------
       Wide screens only. The giant word drifts faster than the portrait;
       transforms only, one frame per scroll burst, idle once the hero is off
       screen. The transforms go on wrapper elements, so they never fight the
       intro animations on the elements inside. */
    function initParallax() {
        var hero = document.querySelector('.hero');
        var word = document.querySelector('.hero-word-wrap');
        var photo = document.querySelector('.hero-parallax');
        if (!hero || !word || !photo || window.innerWidth <= 900 || !('IntersectionObserver' in window)) {
            return;
        }

        var visible = true;
        var ticking = false;
        var frameId;

        var observer = new IntersectionObserver(function (entries) {
            visible = entries[0].isIntersecting;
        });
        observer.observe(hero);

        function update() {
            if (!active) { return; }
            var y = window.scrollY;
            word.style.transform = 'translate3d(0, ' + (y * 0.3).toFixed(1) + 'px, 0)';
            photo.style.transform = 'translate3d(0, ' + (y * 0.12).toFixed(1) + 'px, 0)';
            ticking = false;
        }

        function onScroll() {
            if (visible && !ticking) {
                ticking = true;
                frameId = window.requestAnimationFrame(update);
            }
        }
        window.addEventListener('scroll', onScroll, { passive: true });
        cleanups.push(function () {
            observer.disconnect();
            window.removeEventListener('scroll', onScroll);
            window.cancelAnimationFrame(frameId);
            word.style.transform = '';
            photo.style.transform = '';
        });
    }

    ready(function () {
        if (!active) { return; }
        initCinematic();
        initDetection();
        initCountUp();
        initReveals();
        initMotionLines();
        initParallax();
    });
})();
