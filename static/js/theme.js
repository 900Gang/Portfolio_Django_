/**
 * Theme resolution.
 *
 * Loaded synchronously in <head>, before any painting, so the stored choice
 * is applied to <html> before the first frame. Deferring this to the main
 * bundle would show a flash of the light theme to a dark-mode visitor.
 *
 * Three states are stored: "light", "dark", and absent (follow the OS). The
 * toggle cycles between light and dark; clearing the preference is left to
 * the browser, because a three-way control is more explanation than it is
 * worth for one button.
 */
(function () {
    var STORAGE_KEY = 'portfolio-theme';

    function stored() {
        try {
            return window.localStorage.getItem(STORAGE_KEY);
        } catch (error) {
            // Private mode and blocked site data both throw here. Falling
            // back to the OS preference is the correct behaviour, not an
            // error worth surfacing.
            return null;
        }
    }

    function apply(theme) {
        if (theme === 'light' || theme === 'dark') {
            document.documentElement.setAttribute('data-theme', theme);
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }

    apply(stored());

    // Exposed so navigation.js can drive the toggle without duplicating the
    // storage key or the resolution rules.
    window.portfolioTheme = {
        current: function () {
            var explicit = document.documentElement.getAttribute('data-theme');
            if (explicit) {
                return explicit;
            }
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
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
