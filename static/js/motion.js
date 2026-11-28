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

    /* A decorative intro; interaction always dismisses it. */
    function initCinematic() {
        var scene = document.querySelector('.hero-cinematic');
        if (!scene || motion.matches || document.hidden) {
            return;
        }
        var fallbackTimer;
        var duration = 7250;

        function stop() {
            scene.classList.remove('is-playing');
            document.documentElement.classList.remove('cinematic-active');
            window.clearTimeout(fallbackTimer);
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

        scene.classList.add('is-playing');
        document.documentElement.classList.add('cinematic-active');
        window.addEventListener('pointerdown', stop, { once: true });
        window.addEventListener('keydown', stop, { once: true });
        window.addEventListener('scroll', stop, { once: true, passive: true });
        document.addEventListener('visibilitychange', onVisibilityChange);
        motion.addEventListener('change', onMotionChange);
        fallbackTimer = window.setTimeout(stop, duration + 200);
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
        initParallax();
    });
})();
