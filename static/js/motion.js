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
        function frame(timestamp) {
            if (start === null) {
                start = timestamp;
            }
            var progress = Math.min((timestamp - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = format(target * eased, decimals, pad);
            if (progress < 1) {
                window.requestAnimationFrame(frame);
            }
        }
        window.requestAnimationFrame(frame);
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
        window.setTimeout(function () {
            countTo(score, target, 2, 600, false);
        }, 1450);
    }

    /* --- Stats: count up the first time each one is on screen ------------- */
    function initCountUp() {
        var stats = Array.prototype.slice.call(document.querySelectorAll('[data-count]'));
        if (!stats.length || !('IntersectionObserver' in window)) {
            return;
        }
        var observer = new IntersectionObserver(function (entries) {
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

        new IntersectionObserver(function (entries) {
            visible = entries[0].isIntersecting;
        }).observe(hero);

        function update() {
            var y = window.scrollY;
            word.style.transform = 'translate3d(0, ' + (y * 0.3).toFixed(1) + 'px, 0)';
            photo.style.transform = 'translate3d(0, ' + (y * 0.12).toFixed(1) + 'px, 0)';
            ticking = false;
        }

        window.addEventListener('scroll', function () {
            if (visible && !ticking) {
                ticking = true;
                window.requestAnimationFrame(update);
            }
        }, { passive: true });
    }

    ready(function () {
        initDetection();
        initCountUp();
        initReveals();
        initParallax();
    });
})();
