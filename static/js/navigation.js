/**
 * Site behaviour: mobile menu, theme button, scroll spy, sticky-header
 * state, and dismissible flash messages.
 *
 * Everything degrades to a working page without JavaScript — the menu links
 * are ordinary anchors, the theme follows the OS, and flash messages simply
 * stay on screen.
 */
(function () {
    'use strict';

    var MOBILE_BREAKPOINT = 900;

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

        function close() {
            menu.classList.remove('nav-menu-open');
            toggle.setAttribute('aria-expanded', 'false');
        }

        toggle.addEventListener('click', function (event) {
            event.stopPropagation();
            var open = toggle.getAttribute('aria-expanded') === 'true';
            toggle.setAttribute('aria-expanded', String(!open));
            menu.classList.toggle('nav-menu-open', !open);
        });

        // Choosing a destination should dismiss the panel covering it.
        menu.addEventListener('click', function (event) {
            if (event.target.closest('.nav-link')) {
                close();
            }
        });

        document.addEventListener('click', function (event) {
            if (!toggle.contains(event.target) && !menu.contains(event.target)) {
                close();
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && menu.classList.contains('nav-menu-open')) {
                close();
                toggle.focus();
            }
        });

        // Resizing past the breakpoint leaves the panel class stranded on a
        // menu that is now the desktop bar.
        window.addEventListener('resize', function () {
            if (window.innerWidth > MOBILE_BREAKPOINT) {
                close();
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

    /* --- Sticky header state --------------------------------------------- */
    function initHeader() {
        var header = document.querySelector('.site-header');
        if (!header) {
            return;
        }

        function update() {
            header.classList.toggle('is-stuck', window.scrollY > 8);
        }

        update();
        window.addEventListener('scroll', update, { passive: true });
    }

    /* --- Scroll spy -------------------------------------------------------
       Marks the nav link for whichever section currently owns the top of the
       viewport. IntersectionObserver rather than a scroll handler, so the
       work happens off the main scroll path. */
    function initScrollSpy() {
        var links = Array.prototype.slice.call(
            document.querySelectorAll('.nav-link[href^="#"]')
        );
        if (!links.length || !('IntersectionObserver' in window)) {
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

        var visible = new Set();

        function select() {
            // Of the sections currently in the band, the topmost one wins,
            // so scrolling never highlights a section that has passed.
            var best = null;
            sections.forEach(function (section) {
                if (!visible.has(section.id)) {
                    return;
                }
                if (!best || section.getBoundingClientRect().top < best.getBoundingClientRect().top) {
                    best = section;
                }
            });
            links.forEach(function (link) {
                link.classList.remove('active');
                link.removeAttribute('aria-current');
            });
            if (best && byId[best.id]) {
                byId[best.id].classList.add('active');
                byId[best.id].setAttribute('aria-current', 'true');
            }
        }

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    visible.add(entry.target.id);
                } else {
                    visible.delete(entry.target.id);
                }
            });
            select();
        }, {
            // A band just below the header: a section counts as current once
            // its top clears the nav and until it leaves the upper viewport.
            rootMargin: '-20% 0px -70% 0px',
            threshold: 0
        });

        sections.forEach(function (section) {
            observer.observe(section);
        });
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

    ready(function () {
        initMenu();
        initTheme();
        initHeader();
        initScrollSpy();
        initAlerts();
    });
})();
