/**
 * Site behaviour: mobile menu, theme button, header state, scroll spy, and
 * dismissible flash messages.
 *
 * Everything degrades to a working page without JavaScript: the menu links
 * are ordinary anchors, the theme stays dark, and flash messages simply stay
 * on screen.
 */
(function () {
    'use strict';

    var MOBILE_BREAKPOINT = 1100;

    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    /* --- Mobile menu ----------------------------------------------------- */
    function initMenu() {
        var toggle = document.querySelector('.nav-toggle');
        var menu = document.querySelector('.nav-menu');
        if (!toggle || !menu) {
            return;
        }

        function setOpen(open) {
            menu.classList.toggle('nav-menu-open', open);
            toggle.setAttribute('aria-expanded', String(open));
            toggle.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
            toggle.querySelector('.nav-toggle-label').textContent = open ? 'Close' : 'Menu';
            document.documentElement.classList.toggle('menu-open', open);
            // The overlay covers the page; keep keyboard focus inside it.
            document.querySelectorAll('main, .site-footer').forEach(function (region) {
                region.inert = open;
            });
        }

        toggle.addEventListener('click', function (event) {
            event.stopPropagation();
            setOpen(toggle.getAttribute('aria-expanded') !== 'true');
        });

        // Choosing a destination should dismiss the panel covering it.
        menu.addEventListener('click', function (event) {
            if (event.target.closest('.nav-link')) {
                setOpen(false);
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && menu.classList.contains('nav-menu-open')) {
                setOpen(false);
                toggle.focus();
            }
        });

        // Resizing past the breakpoint leaves the panel class stranded on a
        // menu that is now the desktop bar.
        window.addEventListener('resize', function () {
            if (window.innerWidth > MOBILE_BREAKPOINT) {
                setOpen(false);
            }
        });
    }

    /* --- Theme button ---------------------------------------------------- */
    function initTheme() {
        var button = document.querySelector('.theme-toggle');
        if (!button || !window.portfolioTheme) {
            return;
        }

        function label() {
            var next = window.portfolioTheme.current() === 'dark' ? 'light' : 'dark';
            button.setAttribute('aria-label', 'Switch to ' + next + ' theme');
        }

        label();
        button.addEventListener('click', function () {
            window.portfolioTheme.toggle();
            label();
        });
    }

    /* --- Header and scroll progress -------------------------------------- */
    function initHeader() {
        var header = document.querySelector('.site-header');
        if (!header) {
            return;
        }

        var progress = header.querySelector('.scroll-progress');
        var ticking = false;

        function update() {
            var y = window.scrollY;
            header.classList.toggle('is-stuck', y > 8);
            if (progress) {
                var scrollable = document.documentElement.scrollHeight - window.innerHeight;
                var fraction = scrollable > 0 ? Math.max(0, Math.min(1, y / scrollable)) : 0;
                progress.style.transform = 'scaleX(' + fraction + ')';
            }
            ticking = false;
        }

        function scheduleUpdate() {
            if (!ticking) {
                ticking = true;
                window.requestAnimationFrame(update);
            }
        }

        update();
        window.addEventListener('scroll', scheduleUpdate, { passive: true });
        window.addEventListener('resize', scheduleUpdate);
    }

    /* --- Scroll spy -------------------------------------------------------
       Marks the nav link for whichever section currently owns the top of the
       viewport, including the spaces between sections. Off the home page
       the links are "/#section" and there is nothing to spy on. */
    function initScrollSpy() {
        var links = Array.prototype.slice.call(
            document.querySelectorAll('.nav-link[href^="#"]')
        );
        if (!links.length) {
            return;
        }

        var byId = {};
        var sections = [];
        links.forEach(function (link) {
            var id = link.getAttribute('href').slice(1);
            var section = id && document.getElementById(id);
            if (section) {
                byId[id] = link;
                sections.push(section);
            }
        });
        if (!sections.length) {
            return;
        }

        var ticking = false;

        function select() {
            var best = sections[0];
            var marker = window.innerHeight * 0.3;
            sections.forEach(function (section) {
                if (section.getBoundingClientRect().top <= marker) {
                    best = section;
                }
            });
            if (window.scrollY > 0 && window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 1) {
                best = sections[sections.length - 1];
            }
            links.forEach(function (link) {
                link.classList.remove('active');
                link.removeAttribute('aria-current');
            });
            if (best && byId[best.id]) {
                byId[best.id].classList.add('active');
                byId[best.id].setAttribute('aria-current', 'location');
            }
            ticking = false;
        }

        function scheduleSelect() {
            if (!ticking) {
                ticking = true;
                window.requestAnimationFrame(select);
            }
        }
        select();
        window.addEventListener('scroll', scheduleSelect, { passive: true });
        window.addEventListener('resize', scheduleSelect);
    }

    /* --- Dismissible flash messages -------------------------------------- */
    function initAlerts() {
        document.querySelectorAll('.alert-close').forEach(function (button) {
            button.addEventListener('click', function () {
                var alert = button.closest('.alert');
                if (alert) {
                    alert.remove();
                }
            });
        });
    }

    /* --- Contact form error summary -------------------------------------- */
    function initFormErrorSummary() {
        var summary = document.querySelector('.form-error-summary[data-focus-on-load]');
        if (summary) {
            summary.focus();
        }
    }

    ready(function () {
        initMenu();
        initTheme();
        initHeader();
        initScrollSpy();
        initAlerts();
        initFormErrorSummary();
    });
})();
