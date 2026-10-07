/**
 * Theme resolution.
 *
 * Loaded synchronously in <head>, before any painting, so the stored choice
 * is applied to <html> before the first frame.
 *
 * Dark is the default for every visitor: it is the design, and the hero
 * portrait only works on black. The OS colour-scheme preference is
 * deliberately not consulted. Light is an explicit choice made with the
 * toggle, and it persists.
 *
 * It also sets the motion flag described below, for the same reason: it has
 * to be in place before the first frame.
 */
(function () {
    var STORAGE_KEY = 'portfolio-theme';
    var DEFAULT_THEME = 'dark';

    function stored() {
        try {
            return window.localStorage.getItem(STORAGE_KEY);
        } catch (error) {
            // Private mode and blocked site data both throw here. Falling
            // back to the default is correct, not an error worth surfacing.
            return null;
        }
    }

    function apply(theme) {
        document.documentElement.setAttribute('data-theme', theme === 'light' ? 'light' : 'dark');
    }

    apply(stored() || DEFAULT_THEME);

    // Marks that scripts run, for styles that need navigation.js to undo
    // them (the transparent header over a stage hero).
    document.documentElement.classList.add('js');

    // Motion flag, set before first paint so the hero intro starts from its
    // hidden state instead of flashing its final state first. motion.css
    // scopes every hidden state under this class. If motion.js has not run
    // within three seconds (blocked or failed), the flag is withdrawn so
    // revealed content can never stay invisible.
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduceMotion) {
        document.documentElement.classList.add('motion-ready');
        window.setTimeout(function () {
            if (!window.portfolioMotion) {
                document.documentElement.classList.remove('motion-ready');
            }
        }, 3000);
    }

    // Exposed so navigation.js can drive the toggle without duplicating the
    // storage key or the resolution rules.
    window.portfolioTheme = {
        current: function () {
            return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
        },
        toggle: function () {
            var next = this.current() === 'dark' ? 'light' : 'dark';
            apply(next);
            try {
                window.localStorage.setItem(STORAGE_KEY, next);
            } catch (error) {
                // Preference simply does not persist; the page still switches.
            }
            return next;
        }
    };
})();
