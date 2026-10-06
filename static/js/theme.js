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
