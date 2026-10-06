# Editorial Noir Portfolio Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the portfolio's visual layer with the black-and-red "editorial noir" design (Direction A) without changing models, views or URLs.

**Architecture:** Hand-written CSS split by responsibility (`variables` → `reset` → `base` → `components` → `sections` → `motion` → `responsive`), the home page split into one Django partial per section, and three small vanilla-JS files (`theme.js` in `<head>`, `navigation.js` and `motion.js` deferred). Two Pillow management commands produce the hero portrait WebPs and the link-preview PNG, which are committed to `static/img/`.

**Tech Stack:** Django 5.2 templates, plain CSS (custom properties, `clamp()`, masks), vanilla JavaScript (IntersectionObserver, requestAnimationFrame), Pillow, Google Fonts (Anton, Archivo, IBM Plex Mono).

**Spec:** `docs/superpowers/specs/2026-10-06-portfolio-redesign-design.md`

## Global Constraints

- Branch: `redesign-editorial-noir` (already created; the spec is committed on it).
- Python is `venv/Scripts/python.exe` (Windows, Git Bash). Always run tests as `DEBUG=True venv/Scripts/python.exe manage.py test ...` — the local `.env` sets `DEBUG=False`, which switches static storage to hashed filenames and breaks the template-string assertions.
- No new Python or JS dependencies. No model, migration, view, URL or settings changes.
- Every colour literal (hex or `rgb()`/`rgba()`) lives in `static/css/variables.css` only. CSS keywords `black`, `white` and `transparent` are allowed elsewhere (masks).
- No `var()` on a line that starts with `@media`.
- Every file in `static/css/` must be linked from `templates/base.html`, and every linked file must exist.
- Dark theme on `:root`; light theme under `:root[data-theme="light"]`; every `--color-*` token defined in both; `--color-stage*` tokens identical in both.
- Text red on dark `#ef3b42`; button-fill red `#d61f26`; giant word / quote card `#c8161d`; light-theme red `#b3141b`.
- Fonts: Anton; Archivo 400/500/600; IBM Plex Mono 400/500 — one Google Fonts `<link>` with `display=swap`.
- Motion animates only `transform` and `opacity`. Every "hidden before reveal" state is scoped under `.motion-ready`. `prefers-reduced-motion: reduce` disables all animation.
- `portfolio/tests.py` is the behavioural baseline and is **not edited**. These strings must keep rendering: "About Me", "Computer Science Engineering graduate" (from `SITE_DESCRIPTION`), "AI &amp; Machine Learning", "Python Development", "Real-Time &amp; IoT Data", "Technical Skills", "Featured Projects", "No featured projects yet. Check back soon!", "Journey", "badge", "No education records.", "Certifications", "View Credential", "No certifications listed.", "Professional Skills", "No professional skills listed.", "Get In Touch", and the ids `projects`, `journey`, `education`, `certifications`, `professional-skills`, `contact`. On the project page the exact text "Project links" (lowercase l) and "Project details" must never appear, and `class="project-detail-actions"` only when a link exists.
- Regression-suite markup rules kept: `skills-group-title` is an `h3`; `project-type-badge` / `project-detail-type-badge` hold the type label; exactly four `class="form-group"` and four `class="form-required"`; `class="form-error"` on errors; `.form-trap {` rule in `components.css` with `position: absolute` before its first `}`; `.btn-primary {` defined in exactly one file; `.nav-link.active` in `components.css`; `navigation.js` contains `IntersectionObserver`, `'active'` and `alert-close`; `reset.css` keeps `scroll-padding-top`; 404 contains "This page doesn't exist"; `500.html` contains no `{{` or `{%`; home page ≤ 8 queries and constant.
- Quote text, exactly: "A model is only as good as the data it learns from."
- Process steps, exactly: Data — "Collect, clean and label image and sensor data."; Train — "Build and train models with TensorFlow and Keras."; Evaluate — "Measure accuracy, inspect failure cases, iterate."; Deploy — "Wrap models in Python pipelines and real-time backends."
- Copy deviation from the spec, forced by the baseline tests: the projects heading stays "Featured Projects"; the contact eyebrow is "07 — Get In Touch" above the heading "Let's work together".
- Structural deviation from the spec: each section's breakpoints (1100 / 900 / 760 / 560 px) sit directly under that section in `sections.css`; `responsive.css` keeps only the mobile menu, page-wide small-screen rules and print. Same breakpoints, colocated so a section can be read in one place.
- Between Task 1 and Task 7 the page will look partly unstyled (old markup, new tokens). That is expected; visual verification happens in Task 9.

## Review Focus

1. **Nav links on pages other than home** (project detail, 404). Today they are bare `#about` fragments and go nowhere off the home page. Expected: they lead to the home page section (`/#about`). Pinned in Task 2.
2. **A longer `SITE_ROLE`** (e.g. "Machine Learning Engineer") in the giant hero word. Expected: the word is clipped inside the hero, never causes horizontal scrolling. Pinned in Task 4.
3. **JavaScript blocked, or `motion.js` failing to load.** Expected: every section is visible; nothing stays at `opacity: 0`. Pinned in Task 8.
4. **Light theme over the dark stage** (nav, hero, project hero band). Expected: stage text uses stage tokens, so red-on-black stays readable when the page around it is light. Pinned in Task 1 (identical stage tokens) and Task 4 (hero rules use only stage tokens).
5. **An empty database** (fresh deploy before seeding). Expected: home page renders 200 with every empty state, no ticker band, stats reading `00`. Pinned in Task 6.

---

### Task 1: Tokens, fonts and the dark-by-default theme

**Files:**
- Modify: `static/css/variables.css` (full rewrite)
- Modify: `static/css/reset.css` (token names only)
- Modify: `static/js/theme.js` (full rewrite)
- Modify: `templates/base.html` (head: theme-color, font link; body class block)
- Test: `portfolio/test_regressions.py` (rewrite `ThemeTokenTest`, `ThemeToggleTest`)

**Interfaces:**
- Produces (CSS custom properties used by every later task):
  - Colours: `--color-bg`, `--color-surface`, `--color-surface-raised`, `--color-text-primary`, `--color-text-secondary`, `--color-text-muted`, `--color-border`, `--color-border-strong`, `--color-accent`, `--color-accent-fill`, `--color-accent-fill-hover`, `--color-on-accent`, `--color-accent-deep`, `--color-accent-wash`, `--color-accent-glow`, `--color-stage`, `--color-stage-translucent`, `--color-stage-overlay`, `--color-on-stage`, `--color-on-stage-secondary`, `--color-on-stage-muted`, `--color-stage-accent`, `--color-stage-border`, `--color-status-used`, `--color-status-building`, `--color-status-learning`, `--color-success`, `--color-success-bg`, `--color-success-border`, `--color-error`, `--color-error-bg`, `--color-error-border`.
  - Non-colour: `--font-display`, `--font-body`, `--font-mono`, `--text-2xs` … `--text-display-xl`, `--leading-tight`, `--leading-snug`, `--leading-body`, `--tracking-display`, `--tracking-label`, `--weight-regular|medium|semibold`, `--space-1` … `--space-10`, `--section-pad`, `--shell-max`, `--shell-pad`, `--header-height`, `--radius-sm`, `--radius-pill`, `--border-width`, `--ease-out`, `--dur-fast|base|slow`, `--z-base|raised|header|overlay|grain`, `--texture-grain`, `--grain-opacity`, `--grain-invert`.
- Produces (JS): `window.portfolioTheme.current()` → `'dark' | 'light'`; `window.portfolioTheme.toggle()` → the new theme. `navigation.js` already calls both.
- Produces (template): `{% block body_class %}` on `<body>` in `base.html`.

- [ ] **Step 1: Write the failing tests**

In `portfolio/test_regressions.py`, replace the whole `ThemeTokenTest` class with:

```python
class ThemeTokenTest(TestCase):
    """Colour lives in tokens only, and every colour token exists in both themes."""

    def _variables(self):
        return (BASE_DIR / "static" / "css" / "variables.css").read_text()

    def _blocks(self):
        """(dark, light): dark is everything before the light-theme selector."""
        css = self._variables()
        split = css.index(':root[data-theme="light"]')
        return css[:split], css[split:]

    def test_no_hardcoded_colours_outside_the_token_file(self):
        offenders = []
        for path in (BASE_DIR / "static" / "css").glob("*.css"):
            if path.name == "variables.css":
                continue
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", line):
                    offenders.append(f"{path.name}:{number}: {line.strip()}")
        self.assertEqual(offenders, [])

    def test_every_colour_token_is_defined_in_both_themes(self):
        dark, light = self._blocks()
        dark_tokens = set(re.findall(r"(--color-[a-z-]+):", dark))
        light_tokens = set(re.findall(r"(--color-[a-z-]+):", light))
        self.assertTrue(dark_tokens, "no colour tokens found")
        self.assertEqual(dark_tokens ^ light_tokens, set(), "token missing from one theme")

    def test_dark_is_the_default_and_light_is_explicit(self):
        dark, light = self._blocks()
        self.assertIn("color-scheme: dark", dark)
        self.assertIn("color-scheme: light", light)
        # Dark is the brand look for everyone; the OS preference is not followed.
        self.assertNotIn("prefers-color-scheme", self._variables())

    def test_stage_tokens_are_identical_in_both_themes(self):
        """The hero, nav and quote card stay dark in the light theme, because
        the portrait only works on black."""
        dark, light = self._blocks()
        pattern = r"(--color-(?:stage|on-stage)[a-z-]*):\s*([^;]+);"
        dark_stage = dict(re.findall(pattern, dark))
        self.assertTrue(dark_stage, "no stage tokens found")
        self.assertEqual(dark_stage, dict(re.findall(pattern, light)))

    def test_palette_is_no_longer_stock_bootstrap(self):
        css = self._variables()
        for bootstrap_default in ("#0d6efd", "#198754", "#dc3545", "#212529", "#dee2e6"):
            with self.subTest(colour=bootstrap_default):
                self.assertNotIn(bootstrap_default, css)

    def test_fonts_are_declared_with_fallback_stacks(self):
        css = self._variables()
        for family in ('"Anton"', '"Archivo"', '"IBM Plex Mono"'):
            with self.subTest(family=family):
                self.assertIn(family, css)
        # A webfont that fails to load must still land on a real stack.
        self.assertIn("system-ui", css)
        self.assertIn("monospace", css)

    def test_stylesheet_link_for_the_webfont_is_present(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn("fonts.googleapis.com", html)
        self.assertIn("family=Anton", html)
        self.assertIn("family=Archivo", html)
        self.assertIn("IBM+Plex+Mono", html)
```

Replace the whole `ThemeToggleTest` class with:

```python
class ThemeToggleTest(TestCase):
    """Dark by default; light is a manual choice that persists."""

    def _variables(self):
        return (BASE_DIR / "static" / "css" / "variables.css").read_text()

    def _theme_js(self):
        return (BASE_DIR / "static" / "js" / "theme.js").read_text()

    def test_toggle_control_is_rendered(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn('class="theme-toggle"', html)

    def test_theme_script_runs_before_the_body_to_avoid_a_flash(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        script = html.index("js/theme.js")
        self.assertLess(script, html.index("<body"), "theme.js must be in <head>")
        self.assertNotIn("js/theme.js\" defer", html)

    def test_light_theme_is_an_explicit_override(self):
        self.assertIn(':root[data-theme="light"]', self._variables())

    def test_dark_is_the_default_without_a_stored_choice(self):
        js = self._theme_js()
        self.assertIn("DEFAULT_THEME = 'dark'", js)
        self.assertNotIn("prefers-color-scheme", js)

    def test_stored_preference_reads_are_guarded(self):
        """localStorage throws in private mode and with site data blocked."""
        js = self._theme_js()
        self.assertIn("localStorage", js)
        self.assertIn("catch", js)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_regressions.ThemeTokenTest portfolio.test_regressions.ThemeToggleTest -v 2`
Expected: FAIL — `ValueError: substring not found` from `_blocks()` (no `:root[data-theme="light"]` yet), the font-link test fails on `family=Anton`, and `test_dark_is_the_default_without_a_stored_choice` fails.

- [ ] **Step 3: Rewrite `static/css/variables.css`**

Replace the whole file with:

```css
/* ==========================================================================
   Design tokens — "Editorial noir".

   Every colour in the project is defined here and nowhere else; the test
   suite enforces it. Dark is the default theme and lives on :root. The light
   "paper" theme is an explicit choice made with the toggle and lives under
   [data-theme="light"]. Every --color-* token is defined in both blocks.

   The stage tokens are identical in both themes on purpose: the navigation,
   the hero and the project hero band stay dark, because the portrait only
   works on black.
   ========================================================================== */

:root {
    color-scheme: dark;

    /* --- Ground and surfaces -------------------------------------------- */
    --color-bg: #070707;
    --color-surface: #0f0f0f;
    --color-surface-raised: #151515;

    /* --- Text ------------------------------------------------------------ */
    --color-text-primary: #f2efea;
    --color-text-secondary: #b9b3ad;
    --color-text-muted: #8a847e;

    /* --- Lines ----------------------------------------------------------- */
    --color-border: #262626;
    --color-border-strong: #3a3a3a;

    /* --- Accent: red ------------------------------------------------------
       The reference red measures about 4.5:1 against both black and white,
       which is on the line. Text uses a lighter red and fills a darker one;
       side by side they read as the same colour. */
    --color-accent: #ef3b42;
    --color-accent-fill: #d61f26;
    --color-accent-fill-hover: #b9181e;
    --color-on-accent: #ffffff;
    --color-accent-deep: #c8161d;
    --color-accent-wash: rgba(214, 31, 38, 0.45);
    --color-accent-glow: rgba(239, 59, 66, 0.18);

    /* --- Stage: dark in both themes ------------------------------------- */
    --color-stage: #070707;
    --color-stage-translucent: rgba(7, 7, 7, 0.92);
    --color-stage-overlay: rgba(7, 7, 7, 0.98);
    --color-on-stage: #f2efea;
    --color-on-stage-secondary: #b9b3ad;
    --color-on-stage-muted: #8a847e;
    --color-stage-accent: #ef3b42;
    --color-stage-border: #262626;

    /* --- Skill status dots ----------------------------------------------- */
    --color-status-used: #ef3b42;
    --color-status-building: #f2b544;
    --color-status-learning: #8a847e;

    /* --- Feedback -------------------------------------------------------- */
    --color-success: #5fd39b;
    --color-success-bg: #0d2419;
    --color-success-border: #1f5a3c;
    --color-error: #ff7a7a;
    --color-error-bg: #2a0f10;
    --color-error-border: #6b1d20;

    /* --- Texture (not colours: one tile of white noise, then dimmed) ----- */
    --grain-opacity: 0.06;
    --grain-invert: 0;
}

:root[data-theme="light"] {
    color-scheme: light;

    --color-bg: #f4f1ec;
    --color-surface: #ffffff;
    --color-surface-raised: #ebe6df;

    --color-text-primary: #111111;
    --color-text-secondary: #4a4540;
    --color-text-muted: #6b655f;

    --color-border: #d9d2c8;
    --color-border-strong: #bdb4a8;

    --color-accent: #b3141b;
    --color-accent-fill: #b3141b;
    --color-accent-fill-hover: #8f1016;
    --color-on-accent: #ffffff;
    --color-accent-deep: #c8161d;
    --color-accent-wash: rgba(179, 20, 27, 0.4);
    --color-accent-glow: rgba(179, 20, 27, 0.12);

    --color-stage: #070707;
    --color-stage-translucent: rgba(7, 7, 7, 0.92);
    --color-stage-overlay: rgba(7, 7, 7, 0.98);
    --color-on-stage: #f2efea;
    --color-on-stage-secondary: #b9b3ad;
    --color-on-stage-muted: #8a847e;
    --color-stage-accent: #ef3b42;
    --color-stage-border: #262626;

    --color-status-used: #b3141b;
    --color-status-building: #9a6212;
    --color-status-learning: #6b655f;

    --color-success: #1a7a4f;
    --color-success-bg: #dcefe5;
    --color-success-border: #b6dcc8;
    --color-error: #a33524;
    --color-error-bg: #f8e0dc;
    --color-error-border: #eebeb5;

    --grain-opacity: 0.05;
    --grain-invert: 1;
}

/* Theme-independent tokens. A separate block, so the two colour blocks above
   stay directly comparable line by line. */
:root {
    /* --- Type ------------------------------------------------------------ */
    --font-display: "Anton", "Impact", "Haettenschweiler", "Arial Narrow Bold", system-ui, sans-serif;
    --font-body: "Archivo", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    --font-mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Consolas, monospace;

    --text-2xs: 0.6875rem;
    --text-xs: 0.75rem;
    --text-sm: 0.875rem;
    --text-base: 1rem;
    --text-md: 1.0625rem;
    --text-lg: 1.25rem;
    --text-xl: clamp(1.375rem, 1.1rem + 1vw, 1.875rem);
    --text-statement: clamp(1.5rem, 1.05rem + 1.8vw, 2.5rem);
    --text-display-sm: clamp(2rem, 1.4rem + 2.4vw, 3rem);
    --text-display-md: clamp(2.75rem, 1.6rem + 4.6vw, 5.5rem);
    --text-display-lg: clamp(3.5rem, 2rem + 6vw, 7rem);
    --text-display-xl: clamp(3rem, 16.5vw, 15.5rem);

    --leading-tight: 0.92;
    --leading-snug: 1.2;
    --leading-body: 1.65;
    --tracking-display: 0.01em;
    --tracking-label: 0.12em;

    --weight-regular: 400;
    --weight-medium: 500;
    --weight-semibold: 600;

    /* --- Space ----------------------------------------------------------- */
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-5: 1.5rem;
    --space-6: 2rem;
    --space-7: 3rem;
    --space-8: 4rem;
    --space-9: 6rem;
    --space-10: 8rem;

    --section-pad: clamp(4.5rem, 3rem + 6vw, 8rem);
    --shell-max: 1320px;
    --shell-pad: clamp(1.25rem, 0.5rem + 3vw, 3rem);
    --header-height: 72px;

    /* --- Shape ----------------------------------------------------------- */
    --radius-sm: 2px;
    --radius-pill: 999px;
    --border-width: 1px;

    /* --- Motion ---------------------------------------------------------- */
    --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
    --dur-fast: 160ms;
    --dur-base: 320ms;
    --dur-slow: 800ms;

    /* --- Layers ---------------------------------------------------------- */
    --z-base: 1;
    --z-raised: 3;
    --z-header: 50;
    --z-overlay: 60;
    --z-grain: 100;

    /* --- Texture --------------------------------------------------------
       Film grain: a 160px fractal-noise tile, white with partial alpha. The
       light theme inverts it to dark grain via --grain-invert. */
    --texture-grain: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.6 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23g)'/%3E%3C/svg%3E");
}
```

- [ ] **Step 4: Point `static/css/reset.css` at the new token names**

Make exactly these replacements in `static/css/reset.css` (everything else stays):

| Old | New |
|-----|-----|
| `font-family: var(--font-family-sans-serif);` | `font-family: var(--font-body);` |
| `font-size: var(--font-size-base);` | `font-size: var(--text-base);` |
| `line-height: var(--line-height-normal);` | `line-height: var(--leading-body);` |
| `transition: background-color var(--transition-normal), color var(--transition-normal);` | `transition: background-color var(--dur-base) ease, color var(--dur-base) ease;` |
| `font-weight: var(--font-weight-semibold);` | `font-weight: var(--weight-semibold);` |
| `line-height: var(--line-height-tight);` | `line-height: var(--leading-snug);` |
| `color: var(--color-accent-hover);` (inside `a:hover`) | `color: var(--color-text-primary);` |
| `background-color: var(--color-accent-soft);` (inside `::selection`) | `background-color: var(--color-accent-fill);` |
| `color: var(--color-text-primary);` (inside `::selection`) | `color: var(--color-on-accent);` |

`scroll-padding-top: calc(var(--header-height) + var(--space-5));` stays as is (both tokens still exist).

- [ ] **Step 5: Rewrite `static/js/theme.js`**

Replace the whole file with:

```js
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
```

- [ ] **Step 6: Update the head and body of `templates/base.html`**

Replace the two theme-color lines:

```html
    <meta name="theme-color" content="#fbfcfb" media="(prefers-color-scheme: light)">
    <meta name="theme-color" content="#0c1211" media="(prefers-color-scheme: dark)">
```

with:

```html
    <meta name="theme-color" content="#070707">
```

Replace the comment above the theme script:

```html
    <!-- Resolve the stored theme before first paint. Deferring this would
         show a light-theme flash to a dark-mode visitor. -->
```

with:

```html
    <!-- Resolve the stored theme before first paint, so a visitor who chose
         the light theme never sees a dark frame first. -->
```

Replace the font stylesheet line:

```html
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
```

with:

```html
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
```

Replace `<body>` with:

```html
<body class="{% block body_class %}{% endblock %}">
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_regressions.ThemeTokenTest portfolio.test_regressions.ThemeToggleTest -v 2`
Expected: PASS (12 tests).

- [ ] **Step 8: Run the full suite**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test`
Expected: OK. (`StaticAssetTest.test_no_css_variables_inside_media_query_conditions` and the colour lint still pass: the old `base.css`, `components.css` and `responsive.css` reference undefined tokens now, which only affects rendering, not tests.)

- [ ] **Step 9: Commit**

```bash
git add static/css/variables.css static/css/reset.css static/js/theme.js templates/base.html portfolio/test_regressions.py
git commit -m "Add editorial noir tokens, fonts and dark-by-default theme"
```

---

### Task 2: Page chrome — base layer, components, navigation, footer, responsive

**Files:**
- Modify: `static/css/base.css` (full rewrite)
- Modify: `static/css/components.css` (full rewrite)
- Modify: `static/css/responsive.css` (full rewrite)
- Modify: `static/js/navigation.js` (full rewrite)
- Modify: `templates/components/navigation.html` (full rewrite)
- Modify: `templates/components/footer.html` (full rewrite)
- Modify: `templates/portfolio/home.html` (add one block line)
- Create: `templates/components/icon.html`
- Create: `portfolio/test_redesign.py`
- Modify: `portfolio/test_regressions.py` (`JourneySectionVisibilityTest.test_nav_entry_tracks_the_section_on_detail_pages_too`)

**Interfaces:**
- Consumes: all tokens from Task 1; `{% block body_class %}` from Task 1.
- Produces (CSS classes later tasks use): `.shell`, `.shell-narrow`, `.section`, `.section-head`, `.section-head-text`, `.eyebrow`, `.section-title`, `.section-rule`, `.section-lede`, `.link`, `.icon`, `.visually-hidden`, `.btn`, `.btn-primary`, `.btn-outline`, `.btn-ghost`, `.tech-badge`, `.badge`, project card classes (`.project-card`, `.project-media`, `.project-image`, `.project-image-fallback`, `.project-card-body`, `.project-number`, `.project-card-text`, `.project-type-badge`, `.project-title`, `.project-title-link`, `.project-description`, `.project-tech`, `.project-actions`, `.project-action-link`, `.project-arrow`), form classes (`.contact-form`, `.contact-form-row`, `.form-group`, `.form-label`, `.form-required`, `.form-control`, `.form-error`, `.form-trap`, `.form-actions`, `.form-note`), alerts (`.messages`, `.alert`, `.alert-success`, `.alert-error`, `.alert-close`), `.nav-status-dot`.
- Produces (template): `{% include 'components/icon.html' with name='<name>' %}` renders a decorative 24×24 stroke icon (`<svg class="icon" aria-hidden="true">`). Names: `arrow`, `arrow-left`, `mail`, `code`, `linkedin`, `phone`, `pin`, `data`, `train`, `evaluate`, `deploy`.
- Produces (body class): pages whose top is a dark stage set `{% block body_class %}has-stage-hero{% endblock %}`; the header is then transparent until scrolled.
- Produces (test module): `portfolio/test_redesign.py` with helper `home_html(client) -> str`; later tasks append test classes to it.

- [ ] **Step 1: Write the failing tests**

Create `portfolio/test_redesign.py`:

```python
"""
Tests for the editorial noir redesign
(docs/superpowers/specs/2026-10-06-portfolio-redesign-design.md).

They pin what the new design relies on that the older suites do not cover:
navigation off the home page, the hero, the ticker, the new sections,
motion safety and the image tooling.
"""
import io
import re
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Certification, JourneyEntry, Project, Skill, SkillCategory, SkillStatus

BASE_DIR = Path(settings.BASE_DIR)


def home_html(client):
    return client.get(reverse("portfolio:home")).content.decode()


class ChromeTest(TestCase):
    """Navigation, header and footer shared by every page."""

    def test_nav_links_on_home_stay_on_the_page(self):
        hrefs = re.findall(r'href="([^"]*)" class="nav-link"', home_html(self.client))
        self.assertTrue(hrefs, "no nav links found")
        for href in hrefs:
            with self.subTest(href=href):
                self.assertRegex(href, r"^#[a-z-]+$")

    def test_nav_links_on_other_pages_lead_back_to_home_sections(self):
        project = Project.objects.create(title="P", short_description="d")
        html = self.client.get(project.get_absolute_url()).content.decode()
        hrefs = re.findall(r'href="([^"]*)" class="nav-link"', html)
        self.assertTrue(hrefs, "no nav links found")
        for href in hrefs:
            with self.subTest(href=href):
                self.assertRegex(href, r"^/#[a-z-]+$")

    def test_nav_links_on_the_404_page_lead_back_home_too(self):
        html = self.client.get("/projects/no-such-project/").content.decode()
        hrefs = re.findall(r'href="([^"]*)" class="nav-link"', html)
        self.assertTrue(hrefs, "no nav links found")
        for href in hrefs:
            with self.subTest(href=href):
                self.assertRegex(href, r"^/#[a-z-]+$")

    def test_header_is_transparent_only_over_a_stage_hero(self):
        self.assertIn('<body class="has-stage-hero">', home_html(self.client))
        missing = self.client.get("/projects/no-such-project/").content.decode()
        self.assertNotIn("has-stage-hero", missing)

    def test_header_hides_on_scroll_down_and_returns_on_focus(self):
        js = (BASE_DIR / "static" / "js" / "navigation.js").read_text()
        css = (BASE_DIR / "static" / "css" / "components.css").read_text()
        self.assertIn("'is-hidden'", js)
        self.assertIn(".site-header.is-hidden", css)
        self.assertIn(".site-header:focus-within", css)

    def test_availability_shows_in_the_nav_only_when_set(self):
        self.assertIn('class="nav-status"', home_html(self.client))
        with override_settings(SITE_AVAILABILITY=""):
            self.assertNotIn('class="nav-status"', home_html(self.client))
```

In `portfolio/test_regressions.py`, replace `JourneySectionVisibilityTest.test_nav_entry_tracks_the_section_on_detail_pages_too` with (off the home page the link is now `/#journey`, so the assertion matches the fragment, not the whole `href`):

```python
    def test_nav_entry_tracks_the_section_on_detail_pages_too(self):
        project = Project.objects.create(title="P", short_description="d")
        url = reverse("portfolio:project_detail", kwargs={"slug": project.slug})
        self.assertNotIn('#journey" class="nav-link"', self.client.get(url).content.decode())

        JourneyEntry.objects.create(date="2025-01-01", title="J", description="d")
        self.assertIn('#journey" class="nav-link"', self.client.get(url).content.decode())
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign -v 2`
Expected: FAIL — `test_nav_links_on_other_pages_lead_back_to_home_sections` (hrefs are `#about`), `test_nav_links_on_the_404_page_lead_back_home_too`, `test_header_is_transparent_only_over_a_stage_hero`, `test_header_hides_on_scroll_down_and_returns_on_focus`, `test_availability_shows_in_the_nav_only_when_set`.

- [ ] **Step 3: Create `templates/components/icon.html`**

```django
{# Decorative stroke icon. Usage: {% include 'components/icon.html' with name='mail' %} #}
<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{% if name == 'arrow' %}<path d="M5 12h14M13 6l6 6-6 6"/>{% elif name == 'arrow-left' %}<path d="M19 12H5M11 6l-6 6 6 6"/>{% elif name == 'mail' %}<rect x="3" y="5" width="18" height="14" rx="1"/><path d="M3 7l9 6 9-6"/>{% elif name == 'code' %}<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>{% elif name == 'linkedin' %}<rect x="3" y="3" width="18" height="18" rx="1"/><path d="M8 11v6M8 7.5v.01M12 17v-3.5a2 2 0 0 1 4 0V17M12 11v6"/>{% elif name == 'phone' %}<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>{% elif name == 'pin' %}<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>{% elif name == 'data' %}<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>{% elif name == 'train' %}<circle cx="5" cy="7" r="2"/><circle cx="5" cy="17" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="7" r="2"/><circle cx="19" cy="17" r="2"/><path d="M6.8 8l3.4 3M6.8 16l3.4-3M13.8 11l3.4-3M13.8 13l3.4 3"/>{% elif name == 'evaluate' %}<path d="M4 20h16M7 16v-4M12 16V8M17 16V5"/>{% elif name == 'deploy' %}<path d="M5 19L19 5M9 5h10v10"/>{% endif %}</svg>
```

- [ ] **Step 4: Rewrite `templates/components/navigation.html`**

```django
{# Off the home page the section links point back to it ("/#about"); on the home page they stay in-page ("#about"). #}
{% url 'portfolio:home' as home_url %}
{% if request.path == home_url %}{% firstof "" as nav_base %}{% else %}{% firstof home_url as nav_base %}{% endif %}
<nav class="site-navigation" aria-label="Primary">
    <div class="nav-container">
        <a href="{{ home_url }}" class="nav-logo">{{ site_owner }}<span class="nav-logo-role">{{ site_role }}</span></a>

        <ul class="nav-menu" id="primary-menu">
            <li class="nav-item"><a href="{{ nav_base }}#home" class="nav-link">Home</a></li>
            <li class="nav-item"><a href="{{ nav_base }}#about" class="nav-link">About</a></li>
            <li class="nav-item"><a href="{{ nav_base }}#projects" class="nav-link">Projects</a></li>
            <li class="nav-item"><a href="{{ nav_base }}#skills" class="nav-link">Skills</a></li>
            {% if has_journey_entries %}
            <li class="nav-item"><a href="{{ nav_base }}#journey" class="nav-link">Journey</a></li>
            {% endif %}
            <li class="nav-item"><a href="{{ nav_base }}#education" class="nav-link">Credentials</a></li>
            <li class="nav-item"><a href="{{ nav_base }}#contact" class="nav-link">Contact</a></li>
        </ul>

        <div class="nav-actions">
            {% if site_availability %}
            <span class="nav-status"><span class="nav-status-dot" aria-hidden="true"></span><span class="nav-status-text">{{ site_availability }}</span></span>
            {% endif %}

            {# Labelled from JavaScript, which knows the resolved theme. #}
            <button type="button" class="theme-toggle" aria-label="Switch colour theme">
                <svg class="icon-sun" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <circle cx="12" cy="12" r="4.2"></circle>
                    <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4"></path>
                </svg>
                <svg class="icon-moon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path d="M20.5 14.3A8.5 8.5 0 0 1 9.7 3.5a8.5 8.5 0 1 0 10.8 10.8z"></path>
                </svg>
            </button>

            <button class="nav-toggle" aria-label="Toggle navigation" aria-controls="primary-menu" aria-expanded="false">
                <span class="nav-toggle-icon"></span>
            </button>
        </div>
    </div>
</nav>
```

The Process link is added in Task 5, together with the `#process` section it points at (`NavigationWiringTest` requires every nav anchor to resolve).

- [ ] **Step 5: Rewrite `templates/components/footer.html`**

```django
<div class="footer-content">
    <div class="footer-top">
        <div>
            <p class="footer-identity">{{ site_owner }}</p>
            <p class="footer-tagline">{{ site_role }} · {{ site_location }}. {{ site_focus }}.</p>
        </div>

        <div class="footer-links">
            <a href="{{ site_github_url }}" class="footer-link" target="_blank" rel="noopener noreferrer">GitHub<span class="visually-hidden"> (opens in a new tab)</span></a>
            <a href="{{ site_linkedin_url }}" class="footer-link" target="_blank" rel="noopener noreferrer">LinkedIn<span class="visually-hidden"> (opens in a new tab)</span></a>
            <a href="mailto:{{ site_email }}" class="footer-link">Email</a>
            {% if resume_url %}<a href="{{ resume_url }}" class="footer-link" download="{{ resume_download_name }}">Résumé</a>{% endif %}
        </div>
    </div>

    <div class="footer-bottom">
        <p class="footer-copyright">&copy; {% now "Y" %} {{ site_owner }}. All rights reserved.</p>
        <p class="footer-colophon">Built with Django · Anton, Archivo and IBM Plex Mono</p>
    </div>
</div>
```

- [ ] **Step 6: Mark the home page as a stage-hero page**

In `templates/portfolio/home.html`, directly below the `{% block title %}…{% endblock %}` line, add:

```django
{% block body_class %}has-stage-hero{% endblock %}
```

- [ ] **Step 7: Rewrite `static/css/base.css`**

```css
/* ==========================================================================
   Base — element typography, page scaffolding and shared layout primitives.
   ========================================================================== */

body {
    background-color: var(--color-bg);
    overflow-x: hidden;
}

/* Film grain over the whole page: fixed, non-interactive, no request. */
body::after {
    content: "";
    position: fixed;
    inset: 0;
    z-index: var(--z-grain);
    pointer-events: none;
    background-image: var(--texture-grain);
    opacity: var(--grain-opacity);
    filter: invert(var(--grain-invert));
}

h1,
h2 {
    font-family: var(--font-display);
    font-weight: var(--weight-regular);
    line-height: var(--leading-tight);
    letter-spacing: var(--tracking-display);
    text-transform: uppercase;
}

h3,
h4 {
    font-family: var(--font-body);
    font-weight: var(--weight-semibold);
    line-height: var(--leading-snug);
}

/* --- Page scaffolding --------------------------------------------------- */
.page-wrapper {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* The header is fixed, so ordinary pages start below it. Pages whose top is
   a dark stage let the stage run underneath the transparent header. */
.site-main {
    flex: 1;
    padding-top: var(--header-height);
}

.has-stage-hero .site-main {
    padding-top: 0;
}

.shell {
    width: 100%;
    max-width: var(--shell-max);
    margin-inline: auto;
    padding-inline: var(--shell-pad);
}

.shell-narrow {
    max-width: 52rem;
}

.section {
    padding-block: var(--section-pad);
    border-top: var(--border-width) solid var(--color-border);
}

/* --- Section heading: eyebrow + display title + hairline rule ----------- */
.section-head {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    gap: var(--space-3) var(--space-6);
    margin-bottom: var(--space-7);
}

.section-head-text {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
}

.eyebrow {
    margin: 0;
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-accent);
}

.section-title {
    margin: 0;
    font-size: var(--text-display-md);
}

.section-rule {
    flex: 1 1 8rem;
    height: var(--border-width);
    margin-bottom: 0.9em;
    background: var(--color-border);
}

.section-lede {
    flex-basis: 100%;
    max-width: 60ch;
    margin: 0;
    font-size: var(--text-md);
    color: var(--color-text-secondary);
}

/* --- Small shared pieces ------------------------------------------------- */
.link {
    color: var(--color-accent);
    text-decoration: underline;
    text-underline-offset: 0.2em;
}

.link:hover {
    color: var(--color-text-primary);
}

.icon {
    width: 1.25em;
    height: 1.25em;
    flex: none;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.6;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.visually-hidden {
    position: absolute !important;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
}

.skip-to-content {
    position: absolute;
    top: -100px;
    left: var(--space-4);
    z-index: calc(var(--z-overlay) + 2);
    padding: var(--space-3) var(--space-5);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    text-decoration: none;
    color: var(--color-on-accent);
    background: var(--color-accent-fill);
}

.skip-to-content:focus {
    top: var(--space-4);
    color: var(--color-on-accent);
}
```

- [ ] **Step 8: Rewrite `static/css/components.css`**

```css
/* ==========================================================================
   Components — header and navigation, buttons, chips, project cards, form,
   alerts and footer. Page sections live in sections.css.
   ========================================================================== */

/* --- Header -------------------------------------------------------------
   Always a dark bar (stage tokens), in both themes. Over a stage hero it is
   transparent until the page scrolls. */
.site-header {
    position: fixed;
    inset: 0 0 auto;
    z-index: var(--z-header);
    height: var(--header-height);
    background: var(--color-stage-translucent);
    border-bottom: var(--border-width) solid var(--color-stage-border);
    transition: transform var(--dur-base) var(--ease-out), background-color var(--dur-base) ease, border-color var(--dur-base) ease;
}

.has-stage-hero .site-header:not(.is-stuck) {
    background: transparent;
    border-bottom-color: transparent;
}

.site-header.is-hidden {
    transform: translateY(-100%);
}

/* Keyboard focus inside the header always brings it back. */
.site-header:focus-within {
    transform: none;
}

.nav-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-5);
    height: 100%;
    max-width: var(--shell-max);
    margin-inline: auto;
    padding-inline: var(--shell-pad);
}

.nav-logo {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    white-space: nowrap;
    text-decoration: none;
    color: var(--color-on-stage);
}

.nav-logo:hover {
    color: var(--color-on-stage);
}

.nav-logo-role {
    color: var(--color-on-stage-muted);
}

.nav-logo-role::before {
    content: " / ";
}

.nav-menu {
    display: flex;
    align-items: center;
    gap: clamp(1rem, 2vw, 2rem);
    margin: 0;
    padding: 0;
    list-style: none;
}

.nav-link {
    position: relative;
    padding-block: var(--space-2);
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    text-decoration: none;
    color: var(--color-on-stage-secondary);
    transition: color var(--dur-fast) ease;
}

.nav-link::after {
    content: "";
    position: absolute;
    right: 0;
    bottom: 0;
    left: 0;
    height: var(--border-width);
    background: var(--color-stage-accent);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform var(--dur-base) var(--ease-out);
}

.nav-link:hover,
.nav-link.active {
    color: var(--color-on-stage);
}

.nav-link:hover::after,
.nav-link.active::after {
    transform: scaleX(1);
}

.nav-actions {
    display: flex;
    align-items: center;
    gap: var(--space-4);
}

.nav-status {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    white-space: nowrap;
    color: var(--color-stage-accent);
}

.nav-status-dot {
    width: 6px;
    height: 6px;
    flex: none;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 0 4px var(--color-accent-glow);
}

.theme-toggle,
.nav-toggle {
    display: inline-grid;
    place-items: center;
    width: 40px;
    height: 40px;
    padding: 0;
    border: var(--border-width) solid var(--color-stage-border);
    border-radius: 50%;
    color: var(--color-on-stage);
    cursor: pointer;
    transition: border-color var(--dur-fast) ease, color var(--dur-fast) ease;
}

.theme-toggle:hover,
.nav-toggle:hover {
    border-color: var(--color-stage-accent);
    color: var(--color-stage-accent);
}

.theme-toggle svg {
    width: 18px;
    height: 18px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.6;
    stroke-linecap: round;
}

/* The icon shows the theme the button switches *to*. */
.theme-toggle .icon-moon,
:root[data-theme="light"] .theme-toggle .icon-sun {
    display: none;
}

:root[data-theme="light"] .theme-toggle .icon-moon {
    display: block;
}

.nav-toggle {
    display: none;
}

.nav-toggle-icon,
.nav-toggle-icon::before,
.nav-toggle-icon::after {
    display: block;
    width: 16px;
    height: 1.5px;
    background: currentColor;
    transition: transform var(--dur-base) var(--ease-out), background-color var(--dur-fast) ease;
}

.nav-toggle-icon {
    position: relative;
}

.nav-toggle-icon::before,
.nav-toggle-icon::after {
    content: "";
    position: absolute;
    left: 0;
}

.nav-toggle-icon::before {
    top: -5px;
}

.nav-toggle-icon::after {
    top: 5px;
}

.nav-toggle[aria-expanded="true"] .nav-toggle-icon {
    background: transparent;
}

.nav-toggle[aria-expanded="true"] .nav-toggle-icon::before {
    transform: translateY(5px) rotate(45deg);
}

.nav-toggle[aria-expanded="true"] .nav-toggle-icon::after {
    transform: translateY(-5px) rotate(-45deg);
}

/* --- Buttons -------------------------------------------------------------- */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-3);
    min-height: 48px;
    padding: var(--space-3) var(--space-5);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    text-decoration: none;
    border: var(--border-width) solid transparent;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: background-color var(--dur-fast) ease, color var(--dur-fast) ease, border-color var(--dur-fast) ease, transform var(--dur-fast) ease;
}

.btn:active {
    transform: translateY(1px);
}

.btn .icon {
    transition: transform var(--dur-base) var(--ease-out);
}

.btn:hover .icon {
    transform: translateX(4px);
}

.btn-primary {
    background: var(--color-accent-fill);
    color: var(--color-on-accent);
}

.btn-primary:hover {
    background: var(--color-accent-fill-hover);
    color: var(--color-on-accent);
}

.btn-outline {
    border-color: var(--color-accent);
    color: var(--color-text-primary);
}

.btn-outline:hover {
    background: var(--color-accent-fill);
    border-color: var(--color-accent-fill);
    color: var(--color-on-accent);
}

.btn-ghost {
    padding-inline: 0;
    color: var(--color-text-secondary);
}

.btn-ghost:hover {
    color: var(--color-accent);
}

/* --- Chips and badges ----------------------------------------------------- */
.tech-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.3rem 0.65rem;
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    white-space: nowrap;
    color: var(--color-text-secondary);
    border: var(--border-width) solid var(--color-border);
    border-radius: var(--radius-sm);
}

.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.55rem;
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-accent);
    border: var(--border-width) solid currentColor;
    border-radius: var(--radius-pill);
}

/* --- Project card -----------------------------------------------------------
   The title link is stretched over the whole card; the outbound links sit
   above it on their own layer. */
.project-card {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
}

.project-media {
    position: relative;
    aspect-ratio: 16 / 9;
    overflow: hidden;
    background: var(--color-surface);
    border: var(--border-width) solid var(--color-border);
}

.project-media::after {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--color-accent-wash);
    mix-blend-mode: multiply;
    opacity: 0;
    transition: opacity var(--dur-base) ease;
}

.project-image,
.project-image img {
    width: 100%;
    height: 100%;
}

.project-image img {
    object-fit: cover;
    object-position: top center;
    transition: transform var(--dur-slow) var(--ease-out);
}

.project-card:hover .project-image img,
.project-card:focus-within .project-image img {
    transform: scale(1.04);
}

.project-card:hover .project-media::after,
.project-card:focus-within .project-media::after {
    opacity: 1;
}

.project-image-fallback {
    display: grid;
    place-items: center;
    font-family: var(--font-display);
    font-size: var(--text-display-md);
    color: var(--color-border-strong);
}

.project-card-body {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: start;
    gap: var(--space-5);
}

.project-number {
    font-family: var(--font-display);
    font-size: var(--text-display-sm);
    line-height: 1;
    color: var(--color-accent);
}

.project-card-text {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    min-width: 0;
}

.project-type-badge {
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-text-muted);
}

.project-title {
    margin: 0;
    font-size: var(--text-lg);
    letter-spacing: 0.02em;
    text-transform: uppercase;
}

.project-title-link {
    color: var(--color-text-primary);
    text-decoration: none;
}

.project-title-link:hover {
    color: var(--color-text-primary);
}

.project-title-link::after {
    content: "";
    position: absolute;
    inset: 0;
    z-index: var(--z-base);
}

.project-title-link:focus-visible {
    outline: none;
}

.project-title-link:focus-visible::after {
    outline: 2px solid var(--color-accent);
    outline-offset: 6px;
}

.project-description {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
}

.project-tech {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    margin: var(--space-2) 0 0;
    padding: 0;
    list-style: none;
}

.project-actions {
    position: relative;
    z-index: var(--z-raised);
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-5);
    margin-top: var(--space-2);
}

.project-action-link {
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    text-decoration: none;
    color: var(--color-text-muted);
}

.project-action-link:hover {
    color: var(--color-accent);
}

.project-arrow {
    font-size: var(--text-lg);
    color: var(--color-accent);
    transition: transform var(--dur-base) var(--ease-out);
}

.project-card:hover .project-arrow {
    transform: translateX(6px);
}

/* --- Form ------------------------------------------------------------------ */
.contact-form {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
}

.contact-form-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-5);
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
}

.form-label {
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-text-muted);
}

.form-required {
    margin-left: 0.15em;
    color: var(--color-accent);
}

.form-control {
    width: 100%;
    padding: 0.85rem 1rem;
    font-size: var(--text-base);
    color: var(--color-text-primary);
    background: var(--color-bg);
    border: var(--border-width) solid var(--color-border);
    border-radius: var(--radius-sm);
    transition: border-color var(--dur-fast) ease, box-shadow var(--dur-fast) ease;
}

.form-control::placeholder {
    color: var(--color-text-muted);
}

.form-control:hover {
    border-color: var(--color-border-strong);
}

.form-control:focus {
    outline: none;
    border-color: var(--color-accent);
    box-shadow: 0 0 0 3px var(--color-accent-glow);
}

textarea.form-control {
    min-height: 9rem;
    resize: vertical;
}

.form-group:has(.form-error) .form-control {
    border-color: var(--color-error);
}

.form-error {
    font-size: var(--text-sm);
    color: var(--color-error);
}

.form-error p {
    margin: 0;
}

/* Honeypot: off-screen rather than display:none, which some bots skip. */
.form-trap {
    position: absolute;
    left: -10000px;
    width: 1px;
    height: 1px;
    overflow: hidden;
}

.form-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-5);
}

.form-note {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--color-text-muted);
}

/* --- Alerts ----------------------------------------------------------------- */
.messages {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    margin-bottom: var(--space-5);
}

.alert {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-4);
    padding: var(--space-4) var(--space-5);
    font-size: var(--text-sm);
    color: var(--color-text-primary);
    border: var(--border-width) solid var(--color-border);
    border-left-width: 3px;
}

.alert-success {
    background: var(--color-success-bg);
    border-color: var(--color-success-border);
    border-left-color: var(--color-success);
}

.alert-error {
    background: var(--color-error-bg);
    border-color: var(--color-error-border);
    border-left-color: var(--color-error);
}

.alert-close {
    flex: none;
    padding: 0 var(--space-1);
    font-size: var(--text-lg);
    line-height: 1;
    color: var(--color-text-muted);
    border: 0;
    cursor: pointer;
}

.alert-close:hover {
    color: var(--color-text-primary);
}

/* --- Footer ----------------------------------------------------------------- */
.site-footer {
    border-top: var(--border-width) solid var(--color-border);
}

.footer-content {
    max-width: var(--shell-max);
    margin-inline: auto;
    padding: var(--space-8) var(--shell-pad) var(--space-6);
}

.footer-top {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: var(--space-6);
    padding-bottom: var(--space-6);
    border-bottom: var(--border-width) solid var(--color-border);
}

.footer-identity {
    margin: 0;
    font-family: var(--font-display);
    font-size: var(--text-display-sm);
    line-height: 1;
    text-transform: uppercase;
}

.footer-tagline {
    margin: var(--space-2) 0 0;
    font-size: var(--text-sm);
    color: var(--color-text-muted);
}

.footer-links {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-5);
}

.footer-link {
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    text-decoration: none;
    color: var(--color-text-secondary);
}

.footer-link:hover {
    color: var(--color-accent);
}

.footer-bottom {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: var(--space-3);
    padding-top: var(--space-5);
    font-size: var(--text-xs);
    color: var(--color-text-muted);
}

.footer-bottom p {
    margin: 0;
}
```

- [ ] **Step 9: Rewrite `static/css/responsive.css`**

```css
/* ==========================================================================
   Responsive — the mobile menu, page-wide small-screen overrides and print.
   Section-specific breakpoints sit next to their section in sections.css.
   ========================================================================== */

/* While the mobile menu is open the page behind it does not scroll. */
.menu-open {
    overflow: hidden;
}

@media (max-width: 900px) {
    .nav-toggle {
        display: inline-grid;
    }

    .nav-status-text {
        display: none;
    }

    .nav-logo,
    .nav-actions {
        position: relative;
        z-index: calc(var(--z-overlay) + 1);
    }

    .nav-menu {
        position: fixed;
        inset: 0;
        z-index: var(--z-overlay);
        flex-direction: column;
        align-items: flex-start;
        justify-content: center;
        gap: var(--space-1);
        padding: var(--header-height) var(--shell-pad) var(--space-7);
        background: var(--color-stage-overlay);
        opacity: 0;
        visibility: hidden;
        transition: opacity var(--dur-base) ease, visibility 0s linear var(--dur-base);
    }

    .nav-menu.nav-menu-open {
        opacity: 1;
        visibility: visible;
        transition: opacity var(--dur-base) ease;
    }

    .nav-link {
        font-family: var(--font-display);
        font-size: clamp(2.25rem, 9vw, 3.5rem);
        letter-spacing: var(--tracking-display);
        color: var(--color-on-stage);
    }
}

@media (max-width: 560px) {
    .contact-form-row {
        grid-template-columns: 1fr;
    }

    .nav-logo-role {
        display: none;
    }
}

@media print {
    body::after,
    .site-header,
    .ticker,
    .hero-figure,
    .hero-word-wrap,
    .contact-form,
    .quote-cta {
        display: none !important;
    }

    .hero,
    .project-detail-hero,
    .quote-card {
        min-height: 0;
        background: none !important;
    }

    .hero *,
    .project-detail-hero *,
    .quote-card * {
        color: black !important;
    }

    .section {
        padding-block: 1.5rem;
    }

    a {
        color: inherit;
        text-decoration: underline;
    }
}
```

- [ ] **Step 10: Rewrite `static/js/navigation.js`**

```js
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

        function setOpen(open) {
            menu.classList.toggle('nav-menu-open', open);
            toggle.setAttribute('aria-expanded', String(open));
            document.documentElement.classList.toggle('menu-open', open);
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

    /* --- Header state -----------------------------------------------------
       is-stuck: a solid bar once the page has scrolled. is-hidden: tucked
       away while scrolling down past the first screen, back on any scroll
       up. Never hidden while the mobile menu is open. */
    function initHeader() {
        var header = document.querySelector('.site-header');
        if (!header) {
            return;
        }

        var HIDE_AFTER = 480;
        var lastY = window.scrollY;
        var ticking = false;

        function update() {
            var y = window.scrollY;
            var menuOpen = document.querySelector('.nav-menu.nav-menu-open');
            header.classList.toggle('is-stuck', y > 8);
            if (menuOpen || y < HIDE_AFTER || y < lastY) {
                header.classList.remove('is-hidden');
            } else if (y > lastY + 4) {
                header.classList.add('is-hidden');
            }
            lastY = y;
            ticking = false;
        }

        update();
        window.addEventListener('scroll', function () {
            if (!ticking) {
                ticking = true;
                window.requestAnimationFrame(update);
            }
        }, { passive: true });
    }

    /* --- Scroll spy -------------------------------------------------------
       Marks the nav link for whichever section currently owns the top of the
       viewport. IntersectionObserver rather than a scroll handler, so the
       work happens off the main scroll path. Off the home page the links are
       "/#section" and there is nothing to spy on. */
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
```

- [ ] **Step 11: Run the new tests to verify they pass**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign -v 2`
Expected: PASS (6 tests).

- [ ] **Step 12: Run the full suite**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test`
Expected: OK. In particular `StaticAssetTest.test_button_variants_are_defined_once`, `ContactHoneypotTest.test_the_trap_is_hidden_from_people_and_from_screen_readers`, `NavigationWiringTest` (all three) and `ThemeTokenTest.test_no_hardcoded_colours_outside_the_token_file` pass.

- [ ] **Step 13: Commit**

```bash
git add static/css/base.css static/css/components.css static/css/responsive.css static/js/navigation.js templates/components/navigation.html templates/components/footer.html templates/components/icon.html templates/portfolio/home.html portfolio/test_redesign.py portfolio/test_regressions.py
git commit -m "Rebuild page chrome for the editorial noir design"
```

---

### Task 3: Image assets — hero portrait export and the link-preview card

**Files:**
- Create: `portfolio/templatetags/__init__.py` (empty)
- Create: `portfolio/templatetags/portfolio_extras.py`
- Create: `portfolio/management/commands/make_portrait.py`
- Modify: `portfolio/management/commands/make_og_image.py` (full rewrite)
- Create (generated, committed): `static/img/portrait-480.webp`, `static/img/portrait-768.webp`
- Modify (generated, committed): `static/img/og-image.png`
- Test: `portfolio/test_redesign.py` (append)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - Template filter `handle` in library `portfolio_extras`: `handle(name: str) -> str` — `"Anand N"` → `"anand_n"` (lowercase, whitespace runs become one underscore). Also importable: `from portfolio.templatetags.portfolio_extras import handle`.
  - Command `make_portrait SOURCE [--output-dir DIR] [--quality N]` → writes `portrait-480.webp` and `portrait-768.webp` (default dir `static/img/`). Raises `CommandError` if `SOURCE` is missing.
  - Command `make_og_image [--output PATH] [--photo PATH]` → 1200×630 PNG on `(7, 7, 7)`. Raises `CommandError` if `--photo` is given but missing.
  - Static files `img/portrait-480.webp`, `img/portrait-768.webp` (used by Task 4's hero).

- [ ] **Step 1: Write the failing tests**

Append to `portfolio/test_redesign.py`:

```python
class HandleFilterTest(SimpleTestCase):
    """The label on the hero's detection box, derived from SITE_OWNER."""

    def test_lowercases_and_joins_words_with_underscores(self):
        from .templatetags.portfolio_extras import handle

        self.assertEqual(handle("Anand N"), "anand_n")
        self.assertEqual(handle("  Mary   Ann Lee "), "mary_ann_lee")
        self.assertEqual(handle(""), "")


class PortraitCommandTest(SimpleTestCase):
    """make_portrait exports the hero photo at the widths the template serves."""

    def _source(self, folder, size=(800, 1400)):
        path = Path(folder) / "source.jpg"
        Image.new("RGB", size, (40, 40, 40)).save(path, "JPEG")
        return path

    def test_writes_both_widths_as_webp_keeping_the_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._source(tmp)
            call_command("make_portrait", str(source), "--output-dir", tmp, stdout=io.StringIO())
            for width in (480, 768):
                with self.subTest(width=width):
                    with Image.open(Path(tmp) / f"portrait-{width}.webp") as image:
                        self.assertEqual(image.format, "WEBP")
                        self.assertEqual(image.size, (width, round(1400 * width / 800)))

    def test_missing_source_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CommandError):
                call_command(
                    "make_portrait", str(Path(tmp) / "nope.jpg"),
                    "--output-dir", tmp, stdout=io.StringIO(),
                )


class LinkPreviewCommandTest(SimpleTestCase):
    """make_og_image draws the card in the new palette, with an optional headshot."""

    def test_renders_at_open_graph_size_on_the_dark_ground(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "og.png"
            call_command("make_og_image", "--output", str(out), stdout=io.StringIO())
            with Image.open(out) as image:
                self.assertEqual(image.size, (1200, 630))
                self.assertEqual(image.convert("RGB").getpixel((4, 4)), (7, 7, 7))

    def test_places_the_headshot_on_the_right_when_given_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            photo = Path(tmp) / "head.jpg"
            Image.new("RGB", (400, 400), (0, 120, 255)).save(photo, "JPEG", quality=95)
            out = Path(tmp) / "og.png"
            call_command(
                "make_og_image", "--photo", str(photo), "--output", str(out),
                stdout=io.StringIO(),
            )
            with Image.open(out) as image:
                # Right edge of the photo, clear of the detection box.
                red, _green, blue = image.convert("RGB").getpixel((1200 - 72 - 30, 315))
                self.assertGreater(blue, 200)
                self.assertLess(red, 40)

    def test_missing_photo_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CommandError):
                call_command(
                    "make_og_image", "--photo", str(Path(tmp) / "nope.jpg"),
                    "--output", str(Path(tmp) / "og.png"), stdout=io.StringIO(),
                )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.HandleFilterTest portfolio.test_redesign.PortraitCommandTest portfolio.test_redesign.LinkPreviewCommandTest -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'portfolio.templatetags'`, `CommandError: Unknown command: 'make_portrait'`, the `(7, 7, 7)` pixel assertion (the old card is `(12, 18, 17)`), and `unrecognized arguments: --photo`.

- [ ] **Step 3: Create the filter library**

Create an empty `portfolio/templatetags/__init__.py`.

Create `portfolio/templatetags/portfolio_extras.py`:

```python
"""Template filters for the portfolio templates."""
from django import template

register = template.Library()


@register.filter
def handle(name):
    """'Anand N' -> 'anand_n': the label on the hero's detection box."""
    return "_".join(str(name).lower().split())
```

- [ ] **Step 4: Create `portfolio/management/commands/make_portrait.py`**

```python
"""
Export the hero portrait as the web-sized WebP files the hero serves.

    python manage.py make_portrait design/photos/1000256303.jpg

The original photo stays outside the static tree: design/ is git-ignored,
and everything under static/ is published. The outputs are committed.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps

# Must match the srcset in templates/portfolio/sections/hero.html.
WIDTHS = (480, 768)


class Command(BaseCommand):
    help = 'Export the hero portrait as WebP at the widths the hero serves.'

    def add_arguments(self, parser):
        parser.add_argument('source', help='Path to the original portrait.')
        parser.add_argument('--output-dir', help='Destination folder. Defaults to static/img.')
        parser.add_argument('--quality', type=int, default=82, help='WebP quality (default 82).')

    def handle(self, *args, **options):
        source = Path(options['source'])
        if not source.is_file():
            raise CommandError(f'{source} does not exist.')

        output_dir = Path(options['output_dir']) if options['output_dir'] else (
            Path(settings.BASE_DIR) / 'static' / 'img'
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert('RGB')

        for width in WIDTHS:
            if image.width < width:
                self.stderr.write(self.style.WARNING(
                    f'{source} is only {image.width}px wide; upscaling to {width}px.'
                ))
            height = round(image.height * width / image.width)
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
            destination = output_dir / f'portrait-{width}.webp'
            resized.save(destination, 'WEBP', quality=options['quality'], method=6)
            self.stdout.write(self.style.SUCCESS(
                f'Wrote {destination} ({width}x{height}, {destination.stat().st_size // 1024} KB)'
            ))
```

- [ ] **Step 5: Rewrite `portfolio/management/commands/make_og_image.py`**

```python
"""
Render the link-preview (Open Graph) image.

Social platforms will not render an SVG og:image and do not execute CSS, so
the card has to exist as a raster file. Generating it from the site's own
identity settings — rather than hand-designing one in an image editor —
means it cannot drift out of date when the name, role or tagline changes.

    python manage.py make_og_image --photo design/photos/1000256302.jpg

The headshot is optional; without it the card is text only. Pillow is
already a dependency (ImageField), so this adds no new packages.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw, ImageFont, ImageOps

from portfolio.templatetags.portfolio_extras import handle as detection_handle

# Facebook, LinkedIn, Slack and X all crop toward 1.91:1.
WIDTH, HEIGHT = 1200, 630
MARGIN = 72
PHOTO_SIZE = 470
GAP = 48

# Pulled from the dark theme in variables.css. Duplicated deliberately: the
# generator cannot parse CSS custom properties, and a preview that silently
# stopped matching the site would be worse than one that is pinned.
BG = (7, 7, 7)
ACCENT = (239, 59, 66)
ACCENT_FILL = (214, 31, 38)
TEXT = (242, 239, 234)
MUTED = (138, 132, 126)
RULE = (38, 38, 38)
WHITE = (255, 255, 255)

# Where the face sits inside the square headshot crop, as fractions
# (left, top, right, bottom). Tuned for design/photos/1000256302.jpg.
FACE_BOX = (0.27, 0.18, 0.75, 0.70)

# Preference order: the site's own typefaces if installed, then the closest
# common system faces. Impact stands in for Anton on Windows.
FONT_CANDIDATES = {
    'display': [
        '~/Library/Fonts/Anton-Regular.ttf',
        '/Library/Fonts/Anton-Regular.ttf',
        '/usr/share/fonts/truetype/anton/Anton-Regular.ttf',
        'C:/Windows/Fonts/Anton-Regular.ttf',
        '/System/Library/Fonts/Supplemental/Impact.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Impact.ttf',
        'C:/Windows/Fonts/impact.ttf',
        'C:/Windows/Fonts/ariblk.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ],
    'regular': [
        '~/Library/Fonts/Archivo-Regular.ttf',
        '/usr/share/fonts/truetype/archivo/Archivo-Regular.ttf',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'C:/Windows/Fonts/arial.ttf',
    ],
    'mono': [
        '/Library/Fonts/IBMPlexMono-Medium.ttf',
        '~/Library/Fonts/IBMPlexMono-Medium.ttf',
        '/usr/share/fonts/truetype/ibm-plex/IBMPlexMono-Medium.ttf',
        '/System/Library/Fonts/Supplemental/Courier New Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
        'C:/Windows/Fonts/courbd.ttf',
    ],
}


def _font(kind, size):
    for candidate in FONT_CANDIDATES[kind]:
        path = Path(candidate).expanduser()
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    # Better a legible bitmap card than no preview image at all.
    return ImageFont.load_default()


def _fit(draw, text, kind, size, max_width, minimum=40):
    """The largest font of `kind`, from `size` down, that fits `text`."""
    while size > minimum:
        font = _font(kind, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 4
    return _font(kind, minimum)


def _wrap(draw, text, font, max_width):
    """Greedy word wrap against the rendered width of each candidate line."""
    lines, line = [], ''
    for word in text.split():
        trial = f'{line} {word}'.strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _draw_photo(image, draw, photo_path):
    """The headshot on the right, square-cropped, with the hero's detection box."""
    with Image.open(photo_path) as source:
        photo = ImageOps.fit(
            ImageOps.exif_transpose(source).convert('RGB'),
            (PHOTO_SIZE, PHOTO_SIZE),
            Image.Resampling.LANCZOS,
            centering=(0.5, 0.35),
        )
    left = WIDTH - MARGIN - PHOTO_SIZE
    top = (HEIGHT - PHOTO_SIZE) // 2
    image.paste(photo, (left, top))

    x0 = left + round(PHOTO_SIZE * FACE_BOX[0])
    y0 = top + round(PHOTO_SIZE * FACE_BOX[1])
    x1 = left + round(PHOTO_SIZE * FACE_BOX[2])
    y1 = top + round(PHOTO_SIZE * FACE_BOX[3])
    draw.rectangle([x0, y0, x1, y1], outline=ACCENT, width=2)

    arm = 18
    for corner_x, corner_y, step in ((x0, y0, 1), (x1, y1, -1)):
        draw.line([(corner_x, corner_y), (corner_x + step * arm, corner_y)], fill=ACCENT, width=5)
        draw.line([(corner_x, corner_y), (corner_x, corner_y + step * arm)], fill=ACCENT, width=5)

    label = f'{detection_handle(settings.SITE_OWNER)} · 0.99'
    font = _font('mono', 18)
    label_width = draw.textlength(label, font=font)
    draw.rectangle([x0, y0 - 30, x0 + label_width + 16, y0 - 2], fill=ACCENT_FILL)
    draw.text((x0 + 8, y0 - 26), label, font=font, fill=WHITE)


class Command(BaseCommand):
    help = 'Render the Open Graph link-preview image into the static tree.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            help='Destination path. Defaults to static/<OG_IMAGE_STATIC_PATH>.',
        )
        parser.add_argument(
            '--photo',
            help='Optional headshot placed on the right of the card.',
        )

    def handle(self, *args, **options):
        relative = settings.OG_IMAGE_STATIC_PATH
        if not relative:
            raise CommandError('OG_IMAGE_STATIC_PATH is empty; nothing to render.')

        photo = Path(options['photo']) if options['photo'] else None
        if photo is not None and not photo.is_file():
            raise CommandError(f'{photo} does not exist.')

        destination = Path(options['output']) if options['output'] else (
            Path(settings.BASE_DIR) / 'static' / relative
        )
        destination.parent.mkdir(parents=True, exist_ok=True)

        image = Image.new('RGB', (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(image)

        text_width = WIDTH - 2 * MARGIN
        if photo is not None:
            _draw_photo(image, draw, photo)
            text_width -= PHOTO_SIZE + GAP

        y = MARGIN + 6
        draw.text((MARGIN, y), settings.SITE_ROLE.upper(), font=_font('mono', 24), fill=ACCENT)
        y += 54

        name = settings.SITE_OWNER.upper()
        name_font = _fit(draw, name, 'display', 132, text_width)
        draw.text((MARGIN, y), name, font=name_font, fill=TEXT)
        y += getattr(name_font, 'size', 60) + 26

        draw.rectangle([MARGIN, y, MARGIN + 96, y + 4], fill=ACCENT)
        y += 34

        focus_font = _font('regular', 30)
        for line in _wrap(draw, settings.SITE_FOCUS, focus_font, text_width)[:2]:
            draw.text((MARGIN, y), line, font=focus_font, fill=TEXT)
            y += 42

        y += 10
        description_font = _font('regular', 22)
        for line in _wrap(draw, settings.SITE_DESCRIPTION, description_font, text_width)[:2]:
            draw.text((MARGIN, y), line, font=description_font, fill=MUTED)
            y += 32

        footer_y = HEIGHT - MARGIN - 18
        draw.line(
            [(MARGIN, footer_y - 26), (MARGIN + text_width, footer_y - 26)],
            fill=RULE, width=2,
        )
        footer = ' · '.join(
            part for part in (settings.SITE_LOCATION, settings.SITE_EMAIL) if part
        )
        draw.text((MARGIN, footer_y), footer, font=_font('mono', 20), fill=MUTED)

        image.save(destination, 'PNG', optimize=True)
        self.stdout.write(self.style.SUCCESS(f'Wrote {destination} ({WIDTH}x{HEIGHT})'))
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.HandleFilterTest portfolio.test_redesign.PortraitCommandTest portfolio.test_redesign.LinkPreviewCommandTest -v 2`
Expected: PASS (6 tests).

- [ ] **Step 7: Generate the real assets**

Run:

```bash
venv/Scripts/python.exe manage.py make_portrait design/photos/1000256303.jpg
venv/Scripts/python.exe manage.py make_og_image --photo design/photos/1000256302.jpg
```

Expected output: two `Wrote static/img/portrait-*.webp (…)` lines — the 768 file under about 120 KB, the 480 file under about 60 KB — and `Wrote …og-image.png (1200x630)`.

- [ ] **Step 8: Check the link-preview card by eye**

Open `static/img/og-image.png`. Check: black background, the role in red at top left, the name large in a condensed face, the headshot on the right, and the red detection box framing the face with the `anand_n · 0.99` label above it. If the box misses the face, adjust `FACE_BOX` in `make_og_image.py`, re-run the Step 7 `make_og_image` command, and look again.

- [ ] **Step 9: Run the full suite**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test`
Expected: OK (`LinkPreviewImageTest.test_og_image_file_exists_in_the_static_tree` still passes).

- [ ] **Step 10: Commit**

```bash
git add portfolio/templatetags portfolio/management/commands/make_portrait.py portfolio/management/commands/make_og_image.py static/img/portrait-480.webp static/img/portrait-768.webp static/img/og-image.png portfolio/test_redesign.py
git commit -m "Add portrait export and redraw the link-preview card"
```

---

### Task 4: Hero and skills ticker

**Files:**
- Modify: `portfolio/templatetags/portfolio_extras.py` (add `ticker_skills`)
- Create: `templates/portfolio/sections/hero.html`
- Create: `templates/portfolio/sections/ticker.html`
- Create: `static/css/sections.css`
- Modify: `templates/portfolio/home.html` (replace the inline hero with two includes)
- Modify: `templates/base.html` (link `sections.css`)
- Test: `portfolio/test_redesign.py` (append)

**Interfaces:**
- Consumes: `handle` filter and `img/portrait-480.webp` / `img/portrait-768.webp` (Task 3); stage tokens (Task 1); `.btn`, `.btn-primary`, `.btn-outline`, `.visually-hidden` (Task 2); context `featured_projects`, `skills`, `certifications`, `site_*`, `resume_url`, `resume_download_name` (existing view and context processor).
- Produces:
  - Filter `ticker_skills(skills, limit=16) -> list[Skill]` — skills with status `used_in_projects` first (original order kept), then the rest, capped at `limit`. Never queries.
  - Hero DOM hooks used by Task 8: `.hero`, `.hero-word-wrap`, `.hero-word`, `.hero-figure`, `.hero-parallax`, `.hero-portrait`, `.hero-detect`, `.hero-detect-label`, `.hero-detect-score[data-score]`, `.hero-intro`, `.hero-aside`, `.hero-stat-value[data-count]`.
  - Ticker DOM hooks used by Task 8: `.ticker`, `.ticker-track`, `.ticker-list` (second copy has `aria-hidden="true"`).
  - `static/css/sections.css`, which Tasks 5–7 append to.

- [ ] **Step 1: Write the failing tests**

Append to `portfolio/test_redesign.py`:

```python
class HeroTest(TestCase):
    """The first screen: portrait, giant role word, detection box, stats."""

    def _hero(self):
        html = home_html(self.client)
        start = html.index('<section id="home"')
        return html[start:html.index("</section>", start)]

    def test_portrait_files_exist_in_the_static_tree(self):
        """A missing file would make {% static %} raise under the manifest
        storage in production, taking the whole home page down."""
        for width in (480, 768):
            with self.subTest(width=width):
                self.assertTrue((BASE_DIR / "static" / "img" / f"portrait-{width}.webp").is_file())

    def test_portrait_is_responsive_and_loaded_first(self):
        img = re.search(r'<img class="hero-portrait"[^>]*>', self._hero(), re.S).group(0)
        self.assertRegex(img, r'srcset="[^"]*portrait-480\.webp 480w, [^"]*portrait-768\.webp 768w"')
        self.assertIn('fetchpriority="high"', img)
        self.assertIn('width="768" height="1344"', img)
        self.assertNotIn('loading="lazy"', img)
        self.assertIn(f'alt="Portrait of {settings.SITE_OWNER}"', img)

    def test_decorative_layers_are_hidden_from_assistive_tech(self):
        hero = self._hero()
        self.assertIn('class="hero-word-wrap" aria-hidden="true"', hero)
        self.assertIn('class="hero-detect" aria-hidden="true"', hero)

    def test_detection_label_uses_the_owner_handle(self):
        handle = "_".join(settings.SITE_OWNER.lower().split())
        self.assertIn(f"{handle} · ", self._hero())

    def test_one_h1_and_it_is_the_name(self):
        html = home_html(self.client)
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn(f'<h1 class="hero-title">{settings.SITE_OWNER}</h1>', html)

    def test_stats_count_the_objects_the_page_renders(self):
        for i in range(2):
            Project.objects.create(title=f"P{i}", short_description="d", featured=True)
        for i in range(3):
            Skill.objects.create(name=f"S{i}", category=SkillCategory.BACKEND)
        Certification.objects.create(name="C", issuer="I")
        hero = self._hero()
        for value in (2, 3, 1):
            with self.subTest(value=value):
                self.assertIn(f'data-count="{value}">0{value}</dd>', hero)

    def test_a_long_role_cannot_cause_horizontal_scrolling(self):
        css = (BASE_DIR / "static" / "css" / "sections.css").read_text()
        hero_rule = re.search(r"^\.hero \{([^}]*)\}", css, re.M).group(1)
        self.assertIn("overflow: hidden", hero_rule)
        word_rule = re.search(r"^\.hero-word \{([^}]*)\}", css, re.M).group(1)
        self.assertIn("white-space: nowrap", word_rule)
        with override_settings(SITE_ROLE="Machine Learning Engineer"):
            self.assertIn(
                '<p class="hero-word">Machine Learning Engineer</p>', home_html(self.client)
            )

    def test_hero_rules_use_only_stage_colours(self):
        """In the light theme the page turns light but the hero stays dark, so
        hero rules must never use the page's text, ground or accent tokens."""
        css = (BASE_DIR / "static" / "css" / "sections.css").read_text()
        rules = re.findall(r"^(\.hero[^{]*)\{([^}]*)\}", css, re.M)
        self.assertTrue(rules, "no hero rules found")
        for selector, body in rules:
            with self.subTest(selector=selector.strip()):
                self.assertNotRegex(body, r"var\(--color-(text-|accent\)|bg\)|surface|border)")


class TickerTest(TestCase):
    """The red band of technologies under the hero."""

    def test_used_in_projects_come_first_and_the_list_is_capped(self):
        from .templatetags.portfolio_extras import ticker_skills

        skills = [Skill(name=f"L{i}", status=SkillStatus.LEARNING) for i in range(10)]
        skills += [Skill(name=f"U{i}", status=SkillStatus.USED_IN_PROJECTS) for i in range(10)]
        picked = [skill.name for skill in ticker_skills(skills)]
        self.assertEqual(len(picked), 16)
        self.assertEqual(picked[:10], [f"U{i}" for i in range(10)])

    def test_empty_input_gives_an_empty_ticker(self):
        from .templatetags.portfolio_extras import ticker_skills

        self.assertEqual(ticker_skills([]), [])

    def test_second_copy_is_hidden_from_assistive_tech(self):
        Skill.objects.create(
            name="TensorFlow", category=SkillCategory.BACKEND,
            status=SkillStatus.USED_IN_PROJECTS,
        )
        html = home_html(self.client)
        self.assertEqual(html.count('class="ticker-list"'), 2)
        self.assertIn('class="ticker-list" aria-hidden="true"', html)

    def test_no_band_without_skills(self):
        self.assertNotIn('class="ticker"', home_html(self.client))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.HeroTest portfolio.test_redesign.TickerTest -v 2`
Expected: FAIL/ERROR — the old hero has no `hero-portrait` image or `hero-word` (`AttributeError: 'NoneType' object has no attribute 'group'` and assertion failures), `sections.css` does not exist (`FileNotFoundError`), and `ticker_skills` cannot be imported (`ImportError`). Only `test_portrait_files_exist_in_the_static_tree` and `test_no_band_without_skills` pass already.

- [ ] **Step 3: Add `ticker_skills` to `portfolio/templatetags/portfolio_extras.py`**

Replace the whole file with:

```python
"""Template filters for the portfolio templates."""
from django import template

from ..models import SkillStatus

register = template.Library()

TICKER_LIMIT = 16


@register.filter
def handle(name):
    """'Anand N' -> 'anand_n': the label on the hero's detection box."""
    return "_".join(str(name).lower().split())


@register.filter
def ticker_skills(skills, limit=TICKER_LIMIT):
    """
    The technologies for the ticker under the hero: skills already used in
    projects first, then the rest, capped at `limit`.

    Works on the list the view already fetched, so it adds no query.
    """
    skills = list(skills)
    used = [skill for skill in skills if skill.status == SkillStatus.USED_IN_PROJECTS]
    rest = [skill for skill in skills if skill.status != SkillStatus.USED_IN_PROJECTS]
    return (used + rest)[: int(limit)]
```

- [ ] **Step 4: Create `templates/portfolio/sections/hero.html`**

```django
{% load static portfolio_extras %}
<section id="home" class="hero">
    <div class="hero-word-wrap" aria-hidden="true">
        <p class="hero-word">{{ site_role }}</p>
    </div>

    <div class="hero-figure">
        <div class="hero-parallax">
            <img class="hero-portrait"
                 src="{% static 'img/portrait-768.webp' %}"
                 srcset="{% static 'img/portrait-480.webp' %} 480w, {% static 'img/portrait-768.webp' %} 768w"
                 sizes="(max-width: 900px) 78vw, 34vw"
                 width="768" height="1344"
                 alt="Portrait of {{ site_owner }}"
                 fetchpriority="high"
                 decoding="async">
            <div class="hero-detect" aria-hidden="true">
                <span class="hero-detect-label">{{ site_owner|handle }} · <span class="hero-detect-score" data-score="0.99">0.99</span></span>
            </div>
        </div>
    </div>

    <div class="shell hero-grid">
        <div class="hero-intro">
            <p class="hero-hello">Hello, I'm</p>
            <h1 class="hero-title">{{ site_owner }}</h1>
            <p class="hero-role">{{ site_role }}{% if site_tagline %}<span aria-hidden="true"> · </span>{{ site_tagline }}{% endif %}</p>
            {% if site_current %}
            <p class="hero-current"><span class="hero-current-label">Currently</span>{{ site_current }}</p>
            {% endif %}
            <p class="hero-description">{{ site_description }}</p>
            <div class="hero-actions">
                <a href="#projects" class="btn btn-primary">View projects</a>
                {% if resume_url %}
                <a href="{{ resume_url }}" class="btn btn-outline" download="{{ resume_download_name }}">
                    Download résumé <span class="visually-hidden">(PDF)</span>
                </a>
                {% endif %}
            </div>
        </div>

        <aside class="hero-aside" aria-label="At a glance">
            <p class="hero-statement"><span class="hero-statement-icon" aria-hidden="true">✦</span>Turning image data into models that see, classify and detect.</p>
            <dl class="hero-stats">
                <div class="hero-stat">
                    <dt class="hero-stat-label">Featured projects</dt>
                    <dd class="hero-stat-value" data-count="{{ featured_projects|length }}">{{ featured_projects|length|stringformat:"02d" }}</dd>
                </div>
                <div class="hero-stat">
                    <dt class="hero-stat-label">Technologies</dt>
                    <dd class="hero-stat-value" data-count="{{ skills|length }}">{{ skills|length|stringformat:"02d" }}</dd>
                </div>
                <div class="hero-stat">
                    <dt class="hero-stat-label">Certifications</dt>
                    <dd class="hero-stat-value" data-count="{{ certifications|length }}">{{ certifications|length|stringformat:"02d" }}</dd>
                </div>
            </dl>
        </aside>
    </div>
</section>
```

- [ ] **Step 5: Create `templates/portfolio/sections/ticker.html`**

```django
{% load portfolio_extras %}
{% with ticker=skills|ticker_skills %}
{% if ticker %}
<div class="ticker" role="region" aria-label="Core technologies">
    <div class="ticker-track">
        <ul class="ticker-list">
            {% for skill in ticker %}<li class="ticker-item">{{ skill.name }}</li>{% endfor %}
        </ul>
        {# A second copy makes the loop seamless; it is the same list, so assistive tech skips it. #}
        <ul class="ticker-list" aria-hidden="true">
            {% for skill in ticker %}<li class="ticker-item">{{ skill.name }}</li>{% endfor %}
        </ul>
    </div>
</div>
{% endif %}
{% endwith %}
```

- [ ] **Step 6: Swap the inline hero for the includes in `templates/portfolio/home.html`**

Delete everything from the line `{# ── Hero ──…#}` down to and including the hero's closing `</section>` (the last line before the blank line and `{# ── About ──…#}`). In its place put:

```django
{% include 'portfolio/sections/hero.html' %}
{% include 'portfolio/sections/ticker.html' %}
```

- [ ] **Step 7: Link the new stylesheet in `templates/base.html`**

Directly below `<link rel="stylesheet" href="{% static 'css/components.css' %}">` add:

```html
    <link rel="stylesheet" href="{% static 'css/sections.css' %}">
```

- [ ] **Step 8: Create `static/css/sections.css`**

```css
/* ==========================================================================
   Sections — the home page sections in page order, then the project page and
   the error page. Each section's breakpoints sit directly below it.

   The hero is a "stage": it stays dark in both themes, so every hero rule
   uses only --color-stage*, --color-on-stage* and the red fill tokens.
   ========================================================================== */

/* --- Hero ------------------------------------------------------------------ */
.hero {
    position: relative;
    isolation: isolate;
    display: flex;
    align-items: flex-end;
    min-height: 44rem;
    min-height: max(44rem, 100svh);
    overflow: hidden;
    color: var(--color-on-stage);
    background: var(--color-stage);
}

.hero-word-wrap {
    position: absolute;
    top: calc(var(--header-height) + var(--space-4));
    right: 0;
    left: 0;
    z-index: var(--z-base);
    text-align: center;
    pointer-events: none;
    user-select: none;
}

.hero-word {
    margin: 0;
    font-family: var(--font-display);
    font-size: var(--text-display-xl);
    line-height: 0.86;
    letter-spacing: -0.005em;
    text-transform: uppercase;
    white-space: nowrap;
    color: var(--color-accent-deep);
    -webkit-mask-image: linear-gradient(180deg, black 35%, transparent 96%);
    mask-image: linear-gradient(180deg, black 35%, transparent 96%);
}

.hero-figure {
    position: absolute;
    bottom: 0;
    left: 50%;
    z-index: 2;
    height: 94%;
    aspect-ratio: 768 / 1344;
    transform: translateX(-46%);
    -webkit-mask-image: radial-gradient(ellipse 62% 72% at 50% 38%, black 55%, transparent 80%);
    mask-image: radial-gradient(ellipse 62% 72% at 50% 38%, black 55%, transparent 80%);
}

.hero-parallax {
    position: relative;
    width: 100%;
    height: 100%;
}

.hero-portrait {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* Detection box over the face, in percentages of the photo so it stays on
   the face at every size. Tuned for portrait-*.webp. */
.hero-detect {
    position: absolute;
    top: 18.5%;
    left: 39%;
    width: 23%;
    height: 16.5%;
    border: 1.5px solid var(--color-stage-accent);
}

.hero-detect::before,
.hero-detect::after {
    content: "";
    position: absolute;
    width: 14px;
    height: 14px;
    border: 3px solid var(--color-stage-accent);
}

.hero-detect::before {
    top: -4px;
    left: -4px;
    border-right: 0;
    border-bottom: 0;
}

.hero-detect::after {
    right: -4px;
    bottom: -4px;
    border-top: 0;
    border-left: 0;
}

.hero-detect-label {
    position: absolute;
    bottom: 100%;
    left: -1.5px;
    margin-bottom: 6px;
    padding: 3px 7px;
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    color: var(--color-on-accent);
    background: var(--color-accent-fill);
}

.hero-grid {
    position: relative;
    z-index: var(--z-raised);
    display: grid;
    grid-template-columns: minmax(0, 27rem) 1fr minmax(0, 16rem);
    align-items: end;
    gap: var(--space-6);
    padding-top: calc(var(--header-height) + var(--space-9));
    padding-bottom: var(--space-8);
}

.hero-intro {
    grid-column: 1;
}

.hero-aside {
    grid-column: 3;
    display: flex;
    flex-direction: column;
    gap: var(--space-7);
}

.hero-hello {
    margin: 0 0 var(--space-3);
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-stage-accent);
}

.hero-title {
    margin: 0;
    font-size: var(--text-display-lg);
    color: var(--color-on-stage);
}

.hero-role {
    margin: var(--space-4) 0 0;
    font-size: var(--text-md);
    font-weight: var(--weight-semibold);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--color-stage-accent);
}

.hero-current {
    margin: var(--space-2) 0 0;
    font-size: var(--text-sm);
    color: var(--color-on-stage-secondary);
}

.hero-current-label {
    margin-right: var(--space-2);
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-on-stage-muted);
}

.hero-description {
    max-width: 46ch;
    margin: var(--space-4) 0 0;
    color: var(--color-on-stage-secondary);
}

.hero-actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    margin-top: var(--space-6);
}

.hero .btn-outline {
    color: var(--color-on-stage);
    border-color: var(--color-stage-accent);
}

.hero-statement {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    margin: 0;
    font-size: var(--text-sm);
    color: var(--color-on-stage-secondary);
}

.hero-statement-icon {
    display: grid;
    place-items: center;
    flex: none;
    width: 44px;
    height: 44px;
    color: var(--color-stage-accent);
    border: var(--border-width) solid var(--color-stage-accent);
    border-radius: 50%;
}

.hero-stats {
    margin: 0;
}

.hero-stat {
    display: flex;
    align-items: baseline;
    gap: var(--space-4);
    padding-block: var(--space-4);
    border-top: var(--border-width) solid var(--color-stage-border);
}

.hero-stat-value {
    order: -1;
    min-width: 3.2ch;
    margin: 0;
    font-family: var(--font-display);
    font-size: var(--text-display-sm);
    line-height: 1;
    font-variant-numeric: tabular-nums;
    color: var(--color-stage-accent);
}

.hero-stat-label {
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-on-stage-muted);
}

@media (max-width: 900px) {
    .hero {
        display: block;
        min-height: 0;
    }

    .hero-figure {
        position: relative;
        bottom: auto;
        left: auto;
        width: min(78vw, 26rem);
        height: auto;
        margin: calc(var(--header-height) + 6vw) auto 0;
        transform: none;
    }

    .hero-grid {
        grid-template-columns: 1fr;
        margin-top: -4rem;
        padding-top: 0;
        padding-bottom: var(--space-7);
    }

    .hero-intro,
    .hero-aside {
        grid-column: 1;
    }

    .hero-stats {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: var(--space-4);
    }

    .hero-stat {
        flex-direction: column;
        gap: var(--space-1);
    }
}

@media (max-width: 560px) {
    .hero-actions .btn {
        flex: 1 1 100%;
    }
}

/* --- Skills ticker ----------------------------------------------------------- */
.ticker {
    position: relative;
    z-index: var(--z-raised);
    overflow: hidden;
    color: var(--color-on-accent);
    background: var(--color-accent-fill);
}

.ticker-track {
    display: flex;
    width: max-content;
}

.ticker-list {
    display: flex;
    flex: none;
    align-items: center;
    margin: 0;
    padding: 0 0 0 var(--space-5);
    list-style: none;
}

.ticker-item {
    display: inline-flex;
    align-items: center;
    gap: var(--space-5);
    padding: var(--space-4) var(--space-5) var(--space-4) 0;
    font-family: var(--font-display);
    font-size: var(--text-xl);
    line-height: 1;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    white-space: nowrap;
}

.ticker-item::after {
    content: "✦";
    font-family: var(--font-body);
    font-size: 0.6em;
}
```

- [ ] **Step 9: Run the tests to verify they pass**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.HeroTest portfolio.test_redesign.TickerTest -v 2`
Expected: PASS (12 tests).

- [ ] **Step 10: Run the full suite**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test`
Expected: OK — including `HomePageViewTest.test_homepage_about_section_present` ("Computer Science Engineering graduate" now comes from the hero description), `QueryCountTest.test_homepage_query_count_is_constant`, `ResumeLinkTest` (download link now in the hero) and `StylesheetHygieneTest`.

- [ ] **Step 11: Check the hero in the browser**

Run `DEBUG=True venv/Scripts/python.exe manage.py runserver 8000` in the background (seed first with `venv/Scripts/python.exe manage.py migrate` and `venv/Scripts/python.exe manage.py populate_portfolio` if the local database is empty) and open `http://127.0.0.1:8000/` at 1440×900. Check: the giant red word spans the width behind the photo; the photo's edges fade into black; the red box frames the face with its label just above; name and buttons at left; statement and three stats at right. If the box misses the face, adjust `top`/`left`/`width`/`height` of `.hero-detect` in `sections.css` (percentages of the photo). Then check 390×844: photo above the intro, stats in a row of three, no horizontal scroll.

- [ ] **Step 12: Commit**

```bash
git add portfolio/templatetags/portfolio_extras.py templates/portfolio/sections/hero.html templates/portfolio/sections/ticker.html static/css/sections.css templates/portfolio/home.html templates/base.html portfolio/test_redesign.py
git commit -m "Add the editorial noir hero and skills ticker"
```

---

### Task 5: About, projects and the "How I build" process section

**Files:**
- Create: `templates/portfolio/sections/about.html`
- Create: `templates/portfolio/sections/projects.html`
- Create: `templates/portfolio/sections/process.html`
- Modify: `templates/components/project_card.html` (full rewrite)
- Modify: `templates/components/navigation.html` (add the Process link)
- Modify: `templates/portfolio/home.html` (replace inline About and Projects with three includes)
- Modify: `static/css/sections.css` (append)
- Test: `portfolio/test_redesign.py` (append)

**Interfaces:**
- Consumes: `.section`, `.section-head*`, `.eyebrow`, `.section-title`, `.section-rule`, `.section-lede`, `.btn`, project-card classes and `components/icon.html` (Task 2); `featured_projects` context.
- Produces:
  - `components/project_card.html` takes `project` and `number` (int, 1-based) — `{% include 'components/project_card.html' with number=forloop.counter %}`.
  - `[data-reveal]` attributes on section heads, the About blocks, project cards and process steps (Task 8 animates them; until then they are inert).
  - Section ids `about`, `projects`, `process`.

- [ ] **Step 1: Write the failing tests**

Append to `portfolio/test_redesign.py`:

```python
class AboutAndProjectsTest(TestCase):
    def test_about_leads_with_a_statement_and_keeps_the_highlights(self):
        html = home_html(self.client)
        self.assertIn('class="about-statement"', html)
        titles = re.findall(r'class="highlight-title">(.*?)</h3>', html)
        self.assertEqual(
            titles,
            ["AI &amp; Machine Learning", "Python Development", "Real-Time &amp; IoT Data"],
        )

    def test_project_cards_are_numbered_in_order(self):
        for i in range(2):
            Project.objects.create(title=f"P{i}", short_description="d", featured=True, order=i)
        numbers = re.findall(
            r'class="project-number" aria-hidden="true">(\d+)<', home_html(self.client)
        )
        self.assertEqual(numbers, ["01", "02"])

    def test_card_shows_at_most_four_technologies(self):
        project = Project.objects.create(title="Many", short_description="d", featured=True)
        project.technologies.set(
            [Skill.objects.create(name=f"T{i}", category=SkillCategory.BACKEND) for i in range(6)]
        )
        html = home_html(self.client)
        card = html[html.index('class="project-card"'):]
        card = card[: card.index("</article>")]
        self.assertEqual(card.count('class="tech-badge"'), 4)


class ProcessSectionTest(TestCase):
    def test_four_steps_render_in_order(self):
        titles = re.findall(r'class="process-title">(.*?)</h3>', home_html(self.client))
        self.assertEqual(titles, ["Data", "Train", "Evaluate", "Deploy"])

    def test_step_copy_matches_the_spec(self):
        html = home_html(self.client)
        for line in (
            "Collect, clean and label image and sensor data.",
            "Build and train models with TensorFlow and Keras.",
            "Measure accuracy, inspect failure cases, iterate.",
            "Wrap models in Python pipelines and real-time backends.",
        ):
            with self.subTest(line=line):
                self.assertIn(line, html)

    def test_process_is_linked_from_the_nav(self):
        html = home_html(self.client)
        self.assertIn('href="#process" class="nav-link"', html)
        self.assertIn('<section id="process"', html)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.AboutAndProjectsTest portfolio.test_redesign.ProcessSectionTest -v 2`
Expected: FAIL — no `about-statement`, no `project-number`, five technology badges instead of four (the old card shows them all), no process section or nav link.

- [ ] **Step 3: Rewrite `templates/components/project_card.html`**

```django
{# One featured project. Takes `project` and its 1-based `number`. #}
{% if project %}
<article class="project-card" data-reveal>
    <div class="project-media">
        {% if project.has_image %}
        <figure class="project-image">
            <img src="{{ project.image.url }}" alt="Screenshot of {{ project.title }}" loading="lazy" decoding="async">
        </figure>
        {% else %}
        <div class="project-image project-image-fallback" aria-hidden="true">
            <span>&lt;/&gt;</span>
        </div>
        {% endif %}
    </div>

    <div class="project-card-body">
        <span class="project-number" aria-hidden="true">{{ number|stringformat:"02d" }}</span>

        <div class="project-card-text">
            <span class="project-type-badge">{{ project.project_type }}</span>
            <h3 class="project-title">
                {# Stretched over the whole card in CSS. #}
                <a href="{{ project.get_absolute_url }}" class="project-title-link">{{ project.title }}</a>
            </h3>
            <p class="project-description">{{ project.short_description }}</p>

            {% with project_technologies=project.technologies.all|slice:":4" %}
            {% if project_technologies %}
            <ul class="project-tech" aria-label="Technologies used in {{ project.title }}">
                {% for technology in project_technologies %}
                <li><span class="tech-badge">{{ technology.name }}</span></li>
                {% endfor %}
            </ul>
            {% endif %}
            {% endwith %}

            {% if project.github_url or project.live_demo_url %}
            <div class="project-actions">
                {% if project.github_url %}
                <a href="{{ project.github_url }}" class="project-action-link" target="_blank" rel="noopener noreferrer">
                    GitHub <span class="visually-hidden">(opens in a new tab)</span>
                </a>
                {% endif %}
                {% if project.live_demo_url %}
                <a href="{{ project.live_demo_url }}" class="project-action-link" target="_blank" rel="noopener noreferrer">
                    Live demo <span class="visually-hidden">(opens in a new tab)</span>
                </a>
                {% endif %}
            </div>
            {% endif %}
        </div>

        <span class="project-arrow" aria-hidden="true">{% include 'components/icon.html' with name='arrow' %}</span>
    </div>
</article>
{% endif %}
```

- [ ] **Step 4: Add the Process link to `templates/components/navigation.html`**

Directly below the Projects line:

```django
            <li class="nav-item"><a href="{{ nav_base }}#projects" class="nav-link">Projects</a></li>
```

add:

```django
            <li class="nav-item"><a href="{{ nav_base }}#process" class="nav-link">Process</a></li>
```

- [ ] **Step 5: Create `templates/portfolio/sections/about.html`**

```django
<section id="about" class="about section">
    <div class="shell">
        <div class="section-head" data-reveal>
            <div class="section-head-text">
                <span class="eyebrow">01 — About</span>
                <h2 class="section-title">About Me</h2>
            </div>
            <span class="section-rule" aria-hidden="true"></span>
        </div>

        <div class="about-layout">
            <div class="about-content" data-reveal>
                <p class="about-statement">
                    I’m a B.Tech Computer Science graduate based in Kerala, India, currently
                    an Artificial Intelligence Intern at Yangtso Four Labs. I build things
                    across the stack — from scalable web applications to AI-driven IoT
                    systems — and enjoy breaking monolithic ideas down into clean, efficient
                    code.
                </p>
                <div class="about-body">
                    <p>
                        On the AI side I work the full model lifecycle: preparing and processing
                        image datasets, training and evaluating classifiers with TensorFlow and
                        Keras, and wrapping them in an end-to-end prediction pipeline with
                        OpenCV. Alongside the models I build the systems that feed them — Python
                        backends, REST APIs and real-time pipelines streaming live ESP32 sensor
                        data through Firebase into AI-based detection.
                    </p>
                    <p>
                        Skilled in Python, Java, Flutter, JavaScript and SQL, and familiar with
                        Git, Firebase and TensorFlow, with experience collaborating on
                        four-person project teams. Short term, I want to embed myself in real
                        production workflows and become genuinely expert at writing clean,
                        scalable code; longer term, as I deepen my grasp of system design, I see
                        myself moving toward a technical architect role.
                    </p>
                </div>
            </div>

            <ol class="about-highlights" data-reveal>
                <li class="highlight-item">
                    <span class="highlight-index" aria-hidden="true">01</span>
                    <h3 class="highlight-title">AI &amp; Machine Learning</h3>
                    <p class="highlight-description">Image classification built end to end with TensorFlow, Keras and OpenCV — from dataset preparation to an automated prediction pipeline.</p>
                </li>
                <li class="highlight-item">
                    <span class="highlight-index" aria-hidden="true">02</span>
                    <h3 class="highlight-title">Python Development</h3>
                    <p class="highlight-description">Python backends, data pipelines and prediction workflows, backed by SQL, REST APIs and Django.</p>
                </li>
                <li class="highlight-item">
                    <span class="highlight-index" aria-hidden="true">03</span>
                    <h3 class="highlight-title">Real-Time &amp; IoT Data</h3>
                    <p class="highlight-description">Streaming live ESP32 sensor data through Firebase into an AI detection pipeline, over I2C and a real-time backend.</p>
                </li>
            </ol>
        </div>
    </div>
</section>
```

- [ ] **Step 6: Create `templates/portfolio/sections/projects.html`**

```django
<section id="projects" class="projects section">
    <div class="shell">
        <div class="section-head" data-reveal>
            <div class="section-head-text">
                <span class="eyebrow">02 — Work</span>
                <h2 class="section-title">Featured Projects</h2>
            </div>
            <span class="section-rule" aria-hidden="true"></span>
            <p class="section-lede">
                Systems built end to end — from ESP32 sensor integration and real-time
                data pipelines to model training and the Python that ties them together.
            </p>
        </div>

        {% if featured_projects %}
        <div class="projects-grid">
            {% for project in featured_projects %}
            {% include 'components/project_card.html' with number=forloop.counter %}
            {% endfor %}
        </div>
        {% else %}
        <div class="projects-empty">
            <p class="projects-empty-text">No featured projects yet. Check back soon!</p>
            <a href="#about" class="btn btn-outline">Learn more about me</a>
        </div>
        {% endif %}
    </div>
</section>
```

- [ ] **Step 7: Create `templates/portfolio/sections/process.html`**

```django
<section id="process" class="process section">
    <div class="shell">
        <div class="section-head" data-reveal>
            <div class="section-head-text">
                <span class="eyebrow">03 — Process</span>
                <h2 class="section-title">How I Build</h2>
            </div>
            <span class="section-rule" aria-hidden="true"></span>
            <p class="section-lede">The same four steps behind every model I ship.</p>
        </div>

        <ol class="process-steps">
            <li class="process-step" data-reveal>
                <span class="process-icon">{% include 'components/icon.html' with name='data' %}</span>
                <span class="process-number">01</span>
                <h3 class="process-title">Data</h3>
                <p class="process-text">Collect, clean and label image and sensor data.</p>
            </li>
            <li class="process-step" data-reveal>
                <span class="process-icon">{% include 'components/icon.html' with name='train' %}</span>
                <span class="process-number">02</span>
                <h3 class="process-title">Train</h3>
                <p class="process-text">Build and train models with TensorFlow and Keras.</p>
            </li>
            <li class="process-step" data-reveal>
                <span class="process-icon">{% include 'components/icon.html' with name='evaluate' %}</span>
                <span class="process-number">03</span>
                <h3 class="process-title">Evaluate</h3>
                <p class="process-text">Measure accuracy, inspect failure cases, iterate.</p>
            </li>
            <li class="process-step" data-reveal>
                <span class="process-icon">{% include 'components/icon.html' with name='deploy' %}</span>
                <span class="process-number">04</span>
                <h3 class="process-title">Deploy</h3>
                <p class="process-text">Wrap models in Python pipelines and real-time backends.</p>
            </li>
        </ol>
    </div>
</section>
```

- [ ] **Step 8: Swap the inline About and Projects for includes in `templates/portfolio/home.html`**

Delete everything from the line `{# ── About ──…#}` down to, but not including, the line `{# ── Skills ──…#}`. In its place put:

```django
{% include 'portfolio/sections/about.html' %}
{% include 'portfolio/sections/projects.html' %}
{% include 'portfolio/sections/process.html' %}

```

- [ ] **Step 9: Append to `static/css/sections.css`**

```css

/* --- About --------------------------------------------------------------- */
.about-layout {
    display: grid;
    grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
    align-items: start;
    gap: var(--space-8);
}

.about-statement {
    margin: 0 0 var(--space-6);
    font-size: var(--text-statement);
    font-weight: var(--weight-medium);
    line-height: 1.3;
    letter-spacing: -0.01em;
    color: var(--color-text-primary);
}

.about-body p {
    max-width: 62ch;
    color: var(--color-text-secondary);
}

.about-highlights {
    display: flex;
    flex-direction: column;
    margin: 0;
    padding: 0;
    list-style: none;
    border-top: var(--border-width) solid var(--color-border);
}

.highlight-item {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    gap: var(--space-2) var(--space-5);
    padding-block: var(--space-5);
    border-bottom: var(--border-width) solid var(--color-border);
}

.highlight-index {
    grid-row: span 2;
    font-family: var(--font-display);
    font-size: var(--text-display-sm);
    line-height: 1;
    color: var(--color-accent);
}

.highlight-title {
    margin: 0;
    font-size: var(--text-md);
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.highlight-description {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
}

@media (max-width: 900px) {
    .about-layout {
        grid-template-columns: 1fr;
        gap: var(--space-7);
    }
}

/* --- Projects ------------------------------------------------------------- */
.projects-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-8) var(--space-6);
}

.projects-empty {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-5);
    padding: var(--space-7);
    border: var(--border-width) dashed var(--color-border-strong);
}

.projects-empty-text {
    margin: 0;
    color: var(--color-text-secondary);
}

@media (max-width: 760px) {
    .projects-grid {
        grid-template-columns: 1fr;
    }
}

/* --- Process: how I build -------------------------------------------------- */
.process-steps {
    position: relative;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: var(--space-6);
    margin: 0;
    padding: 0;
    list-style: none;
}

/* The red line that runs behind the four icons on wide screens. */
.process-steps::before {
    content: "";
    position: absolute;
    top: 28px;
    right: 28px;
    left: 28px;
    height: var(--border-width);
    background: var(--color-accent);
}

.process-step {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
}

.process-icon {
    display: grid;
    place-items: center;
    width: 56px;
    height: 56px;
    font-size: 1.25rem;
    color: var(--color-accent);
    background: var(--color-bg);
    border: var(--border-width) solid var(--color-accent);
    border-radius: 50%;
}

.process-number {
    margin-top: var(--space-3);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    letter-spacing: var(--tracking-label);
    color: var(--color-text-muted);
}

.process-title {
    margin: 0;
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: var(--weight-regular);
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: var(--color-text-primary);
}

.process-text {
    max-width: 28ch;
    margin: 0;
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
}

@media (max-width: 900px) {
    .process-steps {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        row-gap: var(--space-7);
    }

    .process-steps::before {
        display: none;
    }
}

@media (max-width: 560px) {
    .process-steps {
        grid-template-columns: 1fr;
    }
}
```

- [ ] **Step 10: Run the tests to verify they pass**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.AboutAndProjectsTest portfolio.test_redesign.ProcessSectionTest -v 2`
Expected: PASS (6 tests).

- [ ] **Step 11: Run the full suite**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test`
Expected: OK — including `HomePageViewTest.test_homepage_projects_section_displays_featured_project`, `ProjectTypeTest`, `AbsoluteUrlTest.test_card_links_through_the_model_method`, `ProjectImageFallbackTest.test_missing_file_renders_the_placeholder_not_a_broken_image`, `NavigationWiringTest.test_every_nav_anchor_resolves_to_a_section_on_the_page` and `QueryCountTest`.

- [ ] **Step 12: Commit**

```bash
git add templates/components/project_card.html templates/components/navigation.html templates/portfolio/sections/about.html templates/portfolio/sections/projects.html templates/portfolio/sections/process.html templates/portfolio/home.html static/css/sections.css portfolio/test_redesign.py
git commit -m "Add About, numbered project cards and the process section"
```

---

### Task 6: Skills, journey, credentials with the quote card, and contact

**Files:**
- Create: `templates/portfolio/sections/skills.html`
- Create: `templates/portfolio/sections/journey.html`
- Create: `templates/portfolio/sections/credentials.html`
- Create: `templates/portfolio/sections/contact.html`
- Modify: `templates/portfolio/home.html` (final form: includes only)
- Modify: `static/css/sections.css` (append)
- Test: `portfolio/test_redesign.py` (append)

**Interfaces:**
- Consumes: shared classes and `components/icon.html` (Task 2), `components/form_field.html` (unchanged), context `skills`, `journey_entries`, `education`, `certifications`, `professional_skills`, `contact_form`, `messages`, `site_*`.
- Produces: section ids `skills`, `journey` (only with entries), `education` (containing `certifications` and `professional-skills`), `contact`; more `[data-reveal]` hooks for Task 8.

- [ ] **Step 1: Write the failing tests**

Append to `portfolio/test_redesign.py`:

```python
class SkillsAndJourneyTest(TestCase):
    def test_skill_status_is_a_dot_plus_text_for_assistive_tech(self):
        Skill.objects.create(
            name="Keras", category=SkillCategory.BACKEND, status=SkillStatus.USED_IN_PROJECTS
        )
        html = home_html(self.client)
        self.assertIn('<span class="skill-dot is-used_in_projects" aria-hidden="true"></span>', html)
        self.assertIn('<span class="visually-hidden">(Used in Projects)</span>', html)

    def test_journey_entries_sit_on_a_timeline(self):
        JourneyEntry.objects.create(date="2025-03-01", title="Joined lab", description="d")
        html = home_html(self.client)
        self.assertIn('<ol class="timeline">', html)
        self.assertIn("March 2025", html)


class CredentialsTest(TestCase):
    def test_quote_card_renders_the_agreed_line(self):
        html = home_html(self.client)
        self.assertIn("A model is only as good as the data it learns from.", html)
        self.assertIn('href="#contact" class="quote-cta"', html)

    def test_certifications_live_inside_the_education_section(self):
        html = home_html(self.client)
        education = html.index('<section id="education"')
        certifications = html.index('id="certifications"')
        contact = html.index('<section id="contact"')
        self.assertLess(education, certifications)
        self.assertLess(certifications, contact)


class ContactTest(TestCase):
    def _contact(self):
        html = home_html(self.client)
        return html[html.index('<section id="contact"'):]

    def test_eyebrow_and_heading(self):
        contact = self._contact()
        self.assertIn("07 — Get In Touch", contact)
        self.assertIn("Let's work", contact)

    def test_channel_icons_are_decorative(self):
        self.assertGreaterEqual(
            self._contact().count('class="icon" viewBox="0 0 24 24" aria-hidden="true"'), 4
        )

    def test_phone_row_only_when_configured(self):
        self.assertIn('href="tel:', self._contact())
        with override_settings(SITE_PHONE=""):
            self.assertNotIn('href="tel:', self._contact())


class EmptyDatabaseTest(TestCase):
    """A fresh deploy, before seeding, still renders a complete page."""

    def test_every_section_renders_its_empty_state(self):
        response = self.client.get(reverse("portfolio:home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for text in (
            "No featured projects yet. Check back soon!",
            "No skills listed.",
            "No education records.",
            "No certifications listed.",
            "No professional skills listed.",
        ):
            with self.subTest(text=text):
                self.assertIn(text, html)
        self.assertNotIn('class="ticker"', html)
        self.assertNotIn('id="journey"', html)
        self.assertEqual(html.count('data-count="0">00</dd>'), 3)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.SkillsAndJourneyTest portfolio.test_redesign.CredentialsTest portfolio.test_redesign.ContactTest portfolio.test_redesign.EmptyDatabaseTest -v 2`
Expected: FAIL — no `skill-dot`, `<ul class="timeline">` instead of `<ol>`, no quote, `id="certifications"` is a separate section, no "07 — Get In Touch" eyebrow or icons. `EmptyDatabaseTest` already passes.

- [ ] **Step 3: Create `templates/portfolio/sections/skills.html`**

```django
<section id="skills" class="skills section">
    <div class="shell">
        <div class="section-head" data-reveal>
            <div class="section-head-text">
                <span class="eyebrow">04 — Skills</span>
                <h2 class="section-title">Technical Skills</h2>
            </div>
            <span class="section-rule" aria-hidden="true"></span>
            <p class="section-lede">Grouped by area, with an honest marker of how far each one has been taken.</p>
        </div>

        {% regroup skills by get_category_display as skills_by_category %}
        {% if skills_by_category %}
        <ul class="skills-legend" aria-label="Status key">
            <li class="skills-legend-item"><span class="skill-dot is-used_in_projects" aria-hidden="true"></span>Used in projects</li>
            <li class="skills-legend-item"><span class="skill-dot is-building_with" aria-hidden="true"></span>Building with</li>
            <li class="skills-legend-item"><span class="skill-dot is-learning" aria-hidden="true"></span>Learning</li>
        </ul>

        <div class="skills-grouped">
            {% for category_group in skills_by_category %}
            <div class="skills-group" data-reveal>
                <h3 class="skills-group-title">{{ category_group.grouper }}</h3>
                <ul class="skills-grid">
                    {% for skill in category_group.list %}
                    <li class="skill-card">
                        <span class="skill-dot is-{{ skill.status }}" aria-hidden="true"></span>
                        <span class="skill-name">{{ skill.name }}</span>
                        <span class="visually-hidden">({{ skill.get_status_display }})</span>
                    </li>
                    {% endfor %}
                </ul>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <p class="skills-empty">No skills listed.</p>
        {% endif %}
    </div>
</section>
```

- [ ] **Step 4: Create `templates/portfolio/sections/journey.html`**

```django
{# Omitted entirely when empty rather than showing visitors an empty state. #}
{% if journey_entries %}
<section id="journey" class="journey section">
    <div class="shell">
        <div class="section-head" data-reveal>
            <div class="section-head-text">
                <span class="eyebrow">05 — Journey</span>
                <h2 class="section-title">Journey</h2>
            </div>
            <span class="section-rule" aria-hidden="true"></span>
        </div>

        <ol class="timeline">
            {% for entry in journey_entries %}
            <li class="timeline-item" data-reveal>
                <div class="timeline-meta">
                    <time class="timeline-date" datetime="{{ entry.date|date:'Y-m-d' }}">{{ entry.date|date:'F Y' }}</time>
                    <span class="timeline-type badge">{{ entry.get_entry_type_display }}</span>
                </div>
                <h3 class="timeline-title">{{ entry.title }}</h3>
                <p class="timeline-description">{{ entry.description|truncatewords:25 }}</p>
            </li>
            {% endfor %}
        </ol>
    </div>
</section>
{% endif %}
```

- [ ] **Step 5: Create `templates/portfolio/sections/credentials.html`**

```django
<section id="education" class="credentials section">
    <div class="shell">
        <div class="section-head" data-reveal>
            <div class="section-head-text">
                <span class="eyebrow">06 — Background</span>
                <h2 class="section-title">Education &amp; Credentials</h2>
            </div>
            <span class="section-rule" aria-hidden="true"></span>
        </div>

        <div class="credentials-grid">
            <div class="credentials-column" data-reveal>
                <h3 class="credentials-column-title">Education</h3>
                {% if education %}
                <ol class="education-list">
                    {% for edu in education %}
                    <li class="education-item">
                        <time class="education-date">{{ edu.start_date.year }} – {% if edu.end_date %}{{ edu.end_date.year }}{% else %}Present{% endif %}</time>
                        <h4 class="education-degree">{{ edu.degree }}</h4>
                        <p class="education-institution">{{ edu.institution }}</p>
                        {% if edu.field_of_study %}
                        <p class="education-field">{{ edu.field_of_study }}</p>
                        {% endif %}
                        {% if edu.description %}
                        <div class="education-description">{{ edu.description|linebreaks }}</div>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ol>
                {% else %}
                <p class="education-empty-text">No education records.</p>
                {% endif %}
            </div>

            <div id="certifications" class="credentials-column" data-reveal>
                <h3 class="credentials-column-title">Certifications</h3>
                {% if certifications %}
                <ul class="certifications-list">
                    {% for cert in certifications %}
                    <li class="certification-item">
                        <div class="certification-info">
                            <h4 class="certification-name">{{ cert.name }}</h4>
                            <p class="certification-issuer">
                                {{ cert.issuer }}{% if cert.issue_year %} · <time class="certification-date">{{ cert.issue_year }}</time>{% endif %}
                            </p>
                        </div>
                        {% if cert.credential_url %}
                        <a href="{{ cert.credential_url }}" class="certification-link" target="_blank" rel="noopener noreferrer">
                            View Credential <span class="visually-hidden">(opens in a new tab)</span>
                        </a>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <p class="certifications-empty-text">No certifications listed.</p>
                {% endif %}

                <section id="professional-skills" class="professional-skills" aria-labelledby="professional-skills-title">
                    <h3 id="professional-skills-title" class="credentials-column-title">Professional Skills</h3>
                    {% if professional_skills %}
                    <div class="professional-skills-list">
                        {% for skill in professional_skills %}
                        <span class="professional-skill-item">{{ skill.name }}</span>
                        {% endfor %}
                    </div>
                    {% else %}
                    <p class="professional-skills-empty-text">No professional skills listed.</p>
                    {% endif %}
                </section>
            </div>

            <figure class="quote-card" data-reveal>
                <span class="quote-mark" aria-hidden="true">“</span>
                <blockquote class="quote-text">
                    <p>A model is only as good as the data it learns from.</p>
                </blockquote>
                <figcaption class="quote-author">— {{ site_owner }}</figcaption>
                <a href="#contact" class="quote-cta">Let's build something {% include 'components/icon.html' with name='arrow' %}</a>
            </figure>
        </div>
    </div>
</section>
```

- [ ] **Step 6: Create `templates/portfolio/sections/contact.html`**

```django
<section id="contact" class="contact section">
    <div class="shell contact-layout">
        <div class="contact-aside" data-reveal>
            <span class="eyebrow">07 — Get In Touch</span>
            <h2 class="section-title contact-title">Let's work <span class="contact-title-accent">together</span></h2>
            <p class="contact-intro">
                Have a role, a project or a question? Use the form, or reach me
                directly on any of these.
            </p>
            {% if site_availability %}
            <p class="contact-availability"><span class="nav-status-dot" aria-hidden="true"></span>{{ site_availability }}</p>
            {% endif %}

            <ul class="contact-channels">
                <li>
                    <a class="contact-channel" href="mailto:{{ site_email }}">
                        <span class="contact-channel-icon">{% include 'components/icon.html' with name='mail' %}</span>
                        <span class="contact-channel-text">
                            <span class="contact-channel-label">Email</span>
                            <span class="contact-channel-value">{{ site_email }}</span>
                        </span>
                    </a>
                </li>
                <li>
                    <a class="contact-channel" href="{{ site_github_url }}" target="_blank" rel="noopener noreferrer">
                        <span class="contact-channel-icon">{% include 'components/icon.html' with name='code' %}</span>
                        <span class="contact-channel-text">
                            <span class="contact-channel-label">GitHub</span>
                            <span class="contact-channel-value">{{ site_github_url|cut:"https://" }}<span class="visually-hidden"> (opens in a new tab)</span></span>
                        </span>
                    </a>
                </li>
                <li>
                    <a class="contact-channel" href="{{ site_linkedin_url }}" target="_blank" rel="noopener noreferrer">
                        <span class="contact-channel-icon">{% include 'components/icon.html' with name='linkedin' %}</span>
                        <span class="contact-channel-text">
                            <span class="contact-channel-label">LinkedIn</span>
                            <span class="contact-channel-value">{{ site_linkedin_url|cut:"https://" }}<span class="visually-hidden"> (opens in a new tab)</span></span>
                        </span>
                    </a>
                </li>
                {% if site_phone %}
                <li>
                    <a class="contact-channel" href="tel:{{ site_phone|cut:' ' }}">
                        <span class="contact-channel-icon">{% include 'components/icon.html' with name='phone' %}</span>
                        <span class="contact-channel-text">
                            <span class="contact-channel-label">Phone</span>
                            <span class="contact-channel-value">{{ site_phone }}</span>
                        </span>
                    </a>
                </li>
                {% endif %}
                <li>
                    <div class="contact-channel">
                        <span class="contact-channel-icon">{% include 'components/icon.html' with name='pin' %}</span>
                        <span class="contact-channel-text">
                            <span class="contact-channel-label">Location</span>
                            <span class="contact-channel-value">{{ site_location }}</span>
                        </span>
                    </div>
                </li>
            </ul>
        </div>

        <div class="contact-content" data-reveal>
            {% if messages %}
            <div class="messages">
                {% for message in messages %}
                <div class="alert alert-{{ message.tags }}">
                    <span>{{ message }}</span>
                    <button class="alert-close" aria-label="Close message" type="button">&times;</button>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <form method="post" action="#contact" class="contact-form" novalidate>
                {% csrf_token %}

                <div class="contact-form-row">
                    {% with field=contact_form.name %}{% include "components/form_field.html" %}{% endwith %}
                    {% with field=contact_form.email %}{% include "components/form_field.html" %}{% endwith %}
                </div>
                {% with field=contact_form.subject %}{% include "components/form_field.html" %}{% endwith %}
                {% with field=contact_form.message %}{% include "components/form_field.html" %}{% endwith %}

                {# Honeypot: off-screen and aria-hidden, so only a bot filling every input trips it. #}
                <div class="form-trap" aria-hidden="true">
                    <label for="{{ contact_form.website.id_for_label }}">{{ contact_form.website.label }}</label>
                    {{ contact_form.website }}
                </div>

                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">Send message {% include 'components/icon.html' with name='arrow' %}</button>
                    <p class="form-note">I usually reply within a couple of days.</p>
                </div>
            </form>
        </div>
    </div>
</section>
```

- [ ] **Step 7: Replace `templates/portfolio/home.html` with its final form**

```django
{% extends 'base.html' %}

{% block title %}{{ site_owner }} — {{ site_role }}{% endblock %}
{% block body_class %}has-stage-hero{% endblock %}

{% block content %}
{% include 'portfolio/sections/hero.html' %}
{% include 'portfolio/sections/ticker.html' %}
{% include 'portfolio/sections/about.html' %}
{% include 'portfolio/sections/projects.html' %}
{% include 'portfolio/sections/process.html' %}
{% include 'portfolio/sections/skills.html' %}
{% include 'portfolio/sections/journey.html' %}
{% include 'portfolio/sections/credentials.html' %}
{% include 'portfolio/sections/contact.html' %}
{% endblock %}
```

- [ ] **Step 8: Append to `static/css/sections.css`**

```css

/* --- Skills ----------------------------------------------------------------- */
.skills-legend {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-5);
    margin: 0 0 var(--space-6);
    padding: 0;
    list-style: none;
}

.skills-legend-item {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-text-muted);
}

.skill-dot {
    width: 8px;
    height: 8px;
    flex: none;
    border-radius: 50%;
    background: var(--color-status-learning);
}

.skill-dot.is-used_in_projects {
    background: var(--color-status-used);
}

.skill-dot.is-building_with {
    background: var(--color-status-building);
}

.skills-grouped {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 19rem), 1fr));
    gap: var(--space-7) var(--space-6);
}

.skills-group {
    padding-top: var(--space-4);
    border-top: var(--border-width) solid var(--color-border);
}

.skills-group-title {
    margin: 0 0 var(--space-4);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-accent);
}

.skills-grid {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    margin: 0;
    padding: 0;
    list-style: none;
}

.skill-card {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: 0.45rem 0.75rem;
    font-size: var(--text-sm);
    background: var(--color-surface);
    border: var(--border-width) solid var(--color-border);
    border-radius: var(--radius-sm);
    transition: border-color var(--dur-fast) ease;
}

.skill-card:hover {
    border-color: var(--color-accent);
}

.skills-empty {
    margin: 0;
    color: var(--color-text-muted);
}

/* --- Journey ------------------------------------------------------------------ */
.timeline {
    position: relative;
    max-width: 56rem;
    margin: 0;
    padding: 0 0 0 var(--space-7);
    list-style: none;
}

.timeline::before {
    content: "";
    position: absolute;
    top: 0.5rem;
    bottom: 0.5rem;
    left: 9px;
    width: var(--border-width);
    background: var(--color-accent);
}

.timeline-item {
    position: relative;
    padding-bottom: var(--space-7);
}

.timeline-item:last-child {
    padding-bottom: 0;
}

.timeline-item::before {
    content: "";
    position: absolute;
    top: 0.35rem;
    left: calc(-1 * var(--space-7) + 2px);
    width: 15px;
    height: 15px;
    background: var(--color-bg);
    border: 2px solid var(--color-accent);
    border-radius: 50%;
}

.timeline-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-3);
    margin-bottom: var(--space-2);
}

.timeline-date {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-text-muted);
}

.timeline-title {
    margin: 0 0 var(--space-2);
    font-size: var(--text-lg);
}

.timeline-description {
    max-width: 62ch;
    margin: 0;
    color: var(--color-text-secondary);
}

/* --- Education and credentials ------------------------------------------------- */
.credentials-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr) minmax(0, 0.9fr);
    align-items: start;
    gap: var(--space-7);
}

.credentials-column {
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
}

.credentials-column-title {
    margin: 0;
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-accent);
}

.education-list,
.certifications-list {
    display: flex;
    flex-direction: column;
    margin: 0;
    padding: 0;
    list-style: none;
}

.education-item,
.certification-item {
    padding-block: var(--space-4);
    border-top: var(--border-width) solid var(--color-border);
}

.education-date {
    display: block;
    margin-bottom: var(--space-2);
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-accent);
}

.education-degree,
.certification-name {
    margin: 0;
    font-size: var(--text-base);
}

.education-institution,
.education-field,
.certification-issuer {
    margin: var(--space-1) 0 0;
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
}

.education-description {
    margin-top: var(--space-2);
    font-size: var(--text-sm);
    color: var(--color-text-muted);
}

.education-description p {
    margin: 0;
}

.certification-item {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-4);
}

.certification-link {
    flex: none;
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    white-space: nowrap;
    text-decoration: none;
    color: var(--color-accent);
}

.certification-link:hover {
    color: var(--color-text-primary);
}

.professional-skills {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
    margin-top: var(--space-5);
}

.professional-skills-list {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
}

.professional-skill-item {
    padding: 0.4rem 0.8rem;
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
    border: var(--border-width) solid var(--color-border-strong);
    border-radius: var(--radius-pill);
}

.education-empty-text,
.certifications-empty-text,
.professional-skills-empty-text {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--color-text-muted);
}

/* The quote card is deep red with white text in both themes. */
.quote-card {
    position: sticky;
    top: calc(var(--header-height) + var(--space-5));
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
    min-height: 26rem;
    margin: 0;
    padding: var(--space-7) var(--space-6);
    color: var(--color-on-accent);
    background: var(--color-accent-deep);
}

.quote-mark {
    font-family: var(--font-display);
    font-size: 6rem;
    line-height: 0.6;
}

.quote-text {
    margin: 0;
}

.quote-text p {
    margin: 0;
    font-size: var(--text-xl);
    font-weight: var(--weight-medium);
    line-height: 1.35;
}

.quote-author {
    margin-top: auto;
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
}

.quote-cta {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding-top: var(--space-4);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    text-decoration: none;
    color: var(--color-on-accent);
    border-top: var(--border-width) solid currentColor;
}

.quote-cta:hover {
    color: var(--color-on-accent);
}

.quote-cta:focus-visible {
    outline-color: var(--color-on-accent);
}

.quote-cta .icon {
    transition: transform var(--dur-base) var(--ease-out);
}

.quote-cta:hover .icon {
    transform: translateX(4px);
}

@media (max-width: 1100px) {
    .credentials-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .quote-card {
        position: static;
        grid-column: 1 / -1;
        min-height: 0;
    }
}

@media (max-width: 760px) {
    .credentials-grid {
        grid-template-columns: 1fr;
    }
}

/* --- Contact ------------------------------------------------------------------- */
.contact-layout {
    display: grid;
    grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
    align-items: start;
    gap: var(--space-8);
}

.contact-title {
    margin: var(--space-3) 0 var(--space-5);
}

.contact-title-accent {
    color: var(--color-accent);
}

.contact-intro {
    max-width: 44ch;
    margin: 0 0 var(--space-5);
    color: var(--color-text-secondary);
}

.contact-availability {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    margin: 0 0 var(--space-6);
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-accent);
}

.contact-channels {
    display: flex;
    flex-direction: column;
    margin: 0;
    padding: 0;
    list-style: none;
    border-top: var(--border-width) solid var(--color-border);
}

.contact-channel {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    padding-block: var(--space-4);
    text-decoration: none;
    color: var(--color-text-primary);
    border-bottom: var(--border-width) solid var(--color-border);
}

a.contact-channel:hover {
    color: var(--color-accent);
}

.contact-channel-icon {
    display: grid;
    place-items: center;
    flex: none;
    width: 44px;
    height: 44px;
    color: var(--color-accent);
    border: var(--border-width) solid var(--color-accent);
    border-radius: 50%;
}

.contact-channel-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.contact-channel-label {
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-text-muted);
}

.contact-channel-value {
    font-size: var(--text-sm);
    overflow-wrap: anywhere;
}

.contact-content {
    padding: var(--space-7);
    background: var(--color-surface);
    border: var(--border-width) solid var(--color-border);
}

@media (max-width: 900px) {
    .contact-layout {
        grid-template-columns: 1fr;
        gap: var(--space-7);
    }
}

@media (max-width: 560px) {
    .contact-content {
        padding: var(--space-5);
    }
}
```

- [ ] **Step 9: Run the tests to verify they pass**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.SkillsAndJourneyTest portfolio.test_redesign.CredentialsTest portfolio.test_redesign.ContactTest portfolio.test_redesign.EmptyDatabaseTest -v 2`
Expected: PASS (8 tests).

- [ ] **Step 10: Run the full suite**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test`
Expected: OK — in particular all of `HomePageViewTest`, `HomepageCertificationsTest`, `HomepageProfessionalSkillsTest`, `ContactFormTest`, `ContactFormRenderingTest`, `ContactHoneypotTest`, `SkillsGroupingTest`, `JourneySectionVisibilityTest` and `QueryCountTest`.

- [ ] **Step 11: Commit**

```bash
git add templates/portfolio/sections/skills.html templates/portfolio/sections/journey.html templates/portfolio/sections/credentials.html templates/portfolio/sections/contact.html templates/portfolio/home.html static/css/sections.css portfolio/test_redesign.py
git commit -m "Add skills, journey, credentials with quote card, and contact sections"
```

---

### Task 7: Project page and error pages

**Files:**
- Modify: `templates/portfolio/project_detail.html` (body class and content block)
- Modify: `templates/404.html` (full rewrite)
- Modify: `templates/500.html` (full rewrite)
- Modify: `static/css/sections.css` (append)
- Test: `portfolio/test_redesign.py` (append)

**Interfaces:**
- Consumes: stage tokens (Task 1); `.shell`, `.shell-narrow`, `.btn*`, `.eyebrow`, `.section-title`, `.section-lede`, `.tech-badge`, `.project-tech`, `.project-image-fallback`, `components/icon.html` (Task 2); `has-stage-hero` header behaviour (Task 2).
- Produces: `.project-detail-hero` stage band; `.error-code`.

- [ ] **Step 1: Write the failing tests**

Append to `portfolio/test_redesign.py`:

```python
class ProjectPageTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Hematology", short_description="Blood smear classifier."
        )

    def _html(self):
        return self.client.get(self.project.get_absolute_url()).content.decode()

    def test_title_sits_in_the_dark_hero_band(self):
        html = self._html()
        start = html.index('class="project-detail-hero"')
        band = html[start:html.index("</header>", start)]
        self.assertIn('<h1 class="project-detail-title">Hematology</h1>', band)
        self.assertIn('<body class="has-stage-hero">', html)

    def test_back_link_returns_to_the_projects_section(self):
        self.assertIn('href="/#projects" class="project-breadcrumb-link"', self._html())


class ErrorPagesTest(TestCase):
    def test_404_shows_the_code_large(self):
        response = self.client.get("/projects/missing/")
        self.assertContains(response, 'class="error-code"', status_code=404)

    def test_500_uses_the_new_palette(self):
        html = (BASE_DIR / "templates" / "500.html").read_text()
        self.assertIn("#070707", html)
        self.assertIn("Anton", html)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.ProjectPageTest portfolio.test_redesign.ErrorPagesTest -v 2`
Expected: FAIL — no `project-detail-hero`, the back link has the old text and class order, no `error-code`, and `500.html` still uses the teal palette.

- [ ] **Step 3: Update `templates/portfolio/project_detail.html`**

Keep every block above `{% block content %}` exactly as it is (title, meta, og, twitter and structured data). Directly above `{% block content %}` add:

```django
{% block body_class %}has-stage-hero{% endblock %}

```

Replace the whole `{% block content %}…{% endblock %}` with:

```django
{% block content %}
<article class="project-detail">
    <header class="project-detail-hero">
        <div class="shell">
            <nav class="project-breadcrumb" aria-label="Breadcrumb">
                <a href="{% url 'portfolio:home' %}#projects" class="project-breadcrumb-link">{% include 'components/icon.html' with name='arrow-left' %} Back to projects</a>
            </nav>
            <span class="project-detail-type-badge">{{ project.project_type }}</span>
            <h1 class="project-detail-title">{{ project.title }}</h1>
            <p class="project-detail-summary">{{ project.short_description }}</p>
        </div>
    </header>

    <div class="shell project-detail-body">
        {% if project.has_image %}
        <figure class="project-detail-image">
            <img src="{{ project.image.url }}" alt="Screenshot of {{ project.title }}">
        </figure>
        {% else %}
        <div class="project-detail-image project-image-fallback" aria-hidden="true">
            <span>&lt;/&gt;</span>
        </div>
        {% endif %}

        <div class="project-detail-layout">
            <div class="project-detail-main">
                {% if project.description %}
                <section class="project-detail-section" aria-labelledby="overview-heading">
                    <h2 id="overview-heading">Overview</h2>
                    <div class="project-detail-description">{{ project.description|linebreaks }}</div>
                </section>
                {% endif %}
            </div>

            <aside class="project-detail-sidebar" aria-label="Project information">
                {% if technologies %}
                <section class="project-detail-section" aria-labelledby="technologies-heading">
                    <h2 id="technologies-heading">Technologies</h2>
                    <ul class="project-tech" aria-label="Technologies used in {{ project.title }}">
                        {% for technology in technologies %}
                        <li><span class="tech-badge">{{ technology.name }}</span></li>
                        {% endfor %}
                    </ul>
                </section>
                {% endif %}

                <section class="project-detail-section" aria-labelledby="project-links-heading">
                    <h2 id="project-links-heading">Links</h2>
                    {% if project.github_url or project.live_demo_url %}
                    <div class="project-detail-actions">
                        {% if project.live_demo_url %}
                        <a href="{{ project.live_demo_url }}" class="btn btn-primary" target="_blank" rel="noopener noreferrer">
                            Live demo <span class="visually-hidden">(opens in a new tab)</span>
                        </a>
                        {% endif %}
                        {% if project.github_url %}
                        <a href="{{ project.github_url }}" class="btn btn-outline" target="_blank" rel="noopener noreferrer">
                            GitHub <span class="visually-hidden">(opens in a new tab)</span>
                        </a>
                        {% endif %}
                    </div>
                    {% else %}
                    <p class="project-links-unavailable">No external links available for this project.</p>
                    {% endif %}
                </section>

                <section class="project-detail-section" aria-labelledby="project-contact-heading">
                    <h2 id="project-contact-heading">Questions?</h2>
                    <p class="project-links-unavailable">
                        Happy to walk through the design decisions —
                        <a href="{% url 'portfolio:home' %}#contact" class="link">get in touch</a>.
                    </p>
                </section>
            </aside>
        </div>
    </div>
</article>
{% endblock %}
```

- [ ] **Step 4: Rewrite `templates/404.html`**

```django
{% extends 'base.html' %}

{% block title %}Page not found — {{ site_owner }}{% endblock %}
{% block meta_description %}The page you were looking for does not exist.{% endblock %}

{% block content %}
<section class="error-page">
    <div class="shell shell-narrow">
        <p class="error-code" aria-hidden="true">404</p>
        <p class="eyebrow">Error 404</p>
        <h1 class="section-title">This page doesn't exist</h1>
        <p class="section-lede">
            The link may be out of date, or the project may have been renamed.
            Everything still lives on the home page.
        </p>
        <div class="error-actions">
            <a href="{% url 'portfolio:home' %}" class="btn btn-primary">Back to home</a>
            <a href="{% url 'portfolio:home' %}#projects" class="btn btn-outline">See projects</a>
        </div>
    </div>
</section>
{% endblock %}
```

- [ ] **Step 5: Rewrite `templates/500.html`**

```html
<!-- Rendered with an empty context by Django's handler500: no context processors and no template tags here. -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Something went wrong</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500&family=IBM+Plex+Mono:wght@500&display=swap">
    <style>
        :root { color-scheme: dark; }
        body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 2rem;
            font-family: 'Archivo', system-ui, -apple-system, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #f2efea;
            background: #070707;
        }
        main { max-width: 42ch; text-align: center; }
        .big {
            margin: 0;
            font-family: 'Anton', Impact, sans-serif;
            font-size: clamp(6rem, 30vw, 14rem);
            line-height: 0.85;
            color: #c8161d;
        }
        .code {
            margin: 1rem 0 0.5rem;
            font-family: 'IBM Plex Mono', ui-monospace, Consolas, monospace;
            font-size: 0.75rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #ef3b42;
        }
        h1 {
            margin: 0 0 0.75rem;
            font-family: 'Anton', Impact, sans-serif;
            font-weight: 400;
            font-size: 2.5rem;
            line-height: 0.95;
            text-transform: uppercase;
        }
        .body { margin: 0 0 1.75rem; color: #b9b3ad; }
        a {
            display: inline-block;
            padding: 0.9rem 1.5rem;
            font-family: 'IBM Plex Mono', ui-monospace, Consolas, monospace;
            font-size: 0.75rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #ffffff;
            background: #d61f26;
            text-decoration: none;
        }
        a:hover { background: #b9181e; }
        a:focus-visible { outline: 2px solid #ef3b42; outline-offset: 3px; }
    </style>
</head>
<body>
    <main>
        <p class="big" aria-hidden="true">500</p>
        <p class="code">Error 500</p>
        <h1>Something went wrong</h1>
        <p class="body">A server error stopped this page from loading. It has been logged — please try again shortly.</p>
        <a href="/">Back to home</a>
    </main>
</body>
</html>
```

- [ ] **Step 6: Append to `static/css/sections.css`**

```css

/* --- Project page ---------------------------------------------------------------
   The title band is a stage, like the home hero: dark in both themes. */
.project-detail-hero {
    padding: calc(var(--header-height) + var(--space-8)) 0 calc(var(--space-8) + var(--space-8));
    color: var(--color-on-stage);
    background: var(--color-stage);
}

.project-breadcrumb {
    margin-bottom: var(--space-6);
}

.project-breadcrumb-link {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    font-family: var(--font-mono);
    font-size: var(--text-2xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    text-decoration: none;
    color: var(--color-on-stage-secondary);
}

.project-breadcrumb-link:hover {
    color: var(--color-stage-accent);
}

.project-detail-type-badge {
    display: inline-block;
    margin-bottom: var(--space-4);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    letter-spacing: var(--tracking-label);
    text-transform: uppercase;
    color: var(--color-stage-accent);
}

.project-detail-title {
    max-width: 18ch;
    margin: 0;
    font-size: var(--text-display-md);
    color: var(--color-on-stage);
}

.project-detail-summary {
    max-width: 60ch;
    margin: var(--space-5) 0 0;
    font-size: var(--text-md);
    color: var(--color-on-stage-secondary);
}

.project-detail-body {
    padding-bottom: var(--section-pad);
}

/* Pulled up so the screenshot overlaps the bottom of the dark band. */
.project-detail-image {
    position: relative;
    aspect-ratio: 16 / 9;
    margin: calc(-1 * var(--space-8)) 0 var(--space-8);
    overflow: hidden;
    background: var(--color-surface);
    border: var(--border-width) solid var(--color-border);
}

.project-detail-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top center;
}

.project-detail-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 20rem);
    gap: var(--space-8);
}

.project-detail-section + .project-detail-section {
    margin-top: var(--space-7);
}

.project-detail-section h2 {
    margin: 0 0 var(--space-4);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    letter-spacing: var(--tracking-label);
    color: var(--color-accent);
}

.project-detail-description {
    max-width: 68ch;
    font-size: var(--text-md);
    color: var(--color-text-secondary);
}

.project-detail-actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
}

.project-links-unavailable {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--color-text-muted);
}

@media (max-width: 900px) {
    .project-detail-layout {
        grid-template-columns: 1fr;
    }
}

/* --- Error page ------------------------------------------------------------------ */
.error-page {
    padding-block: var(--section-pad);
}

.error-code {
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(7rem, 30vw, 20rem);
    line-height: 0.85;
    color: var(--color-accent-deep);
}

.error-page .eyebrow {
    margin-top: var(--space-5);
}

.error-page .section-title {
    margin: var(--space-3) 0 var(--space-4);
}

.error-actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    margin-top: var(--space-6);
}
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.ProjectPageTest portfolio.test_redesign.ErrorPagesTest -v 2`
Expected: PASS (4 tests).

- [ ] **Step 8: Run the full suite**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test`
Expected: OK — in particular `ProjectDetailViewTest` (all), `ProjectTypeTest`, `DocumentHeadTest.test_detail_page_overrides_title_and_description`, `StructuredDataTest`, `ErrorPageTest` (both), `ChromeTest.test_header_is_transparent_only_over_a_stage_hero` and `QueryCountTest.test_project_detail_query_count_is_constant`.

- [ ] **Step 9: Commit**

```bash
git add templates/portfolio/project_detail.html templates/404.html templates/500.html static/css/sections.css portfolio/test_redesign.py
git commit -m "Restyle the project page and error pages"
```

---

### Task 8: Motion

**Files:**
- Create: `static/css/motion.css`
- Create: `static/js/motion.js`
- Modify: `static/js/theme.js` (add the motion flag)
- Modify: `templates/base.html` (link `motion.css`, load `motion.js`)
- Test: `portfolio/test_redesign.py` (append)

**Interfaces:**
- Consumes: hero and ticker hooks (Task 4); `[data-reveal]` (Tasks 5–6); `[data-count]` and `.hero-detect-score[data-score]` (Task 4).
- Produces: `.motion-ready` on `<html>` (set by `theme.js`, withdrawn after 3 s if `window.portfolioMotion` is not set); `window.portfolioMotion = true` (set first thing by `motion.js`); `.is-revealed` added to `[data-reveal]` elements; CSS custom property `--reveal-delay` set per element.

- [ ] **Step 1: Write the failing tests**

Append to `portfolio/test_redesign.py`:

```python
def _strip_keyframes(css):
    """Remove every @keyframes block (balanced braces) from a stylesheet."""
    out, position = [], 0
    while True:
        start = css.find("@keyframes", position)
        if start == -1:
            out.append(css[position:])
            return "".join(out)
        out.append(css[position:start])
        depth, index = 0, css.index("{", start)
        while True:
            if css[index] == "{":
                depth += 1
            elif css[index] == "}":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        position = index + 1


class MotionTest(TestCase):
    """Motion must never cost a visitor content or comfort."""

    def _css(self):
        return (BASE_DIR / "static" / "css" / "motion.css").read_text()

    def test_reduced_motion_switches_animation_off(self):
        css = self._css()
        block = css[css.index("@media (prefers-reduced-motion: reduce)"):]
        self.assertIn("animation-duration: 0.01ms !important", block)
        self.assertIn("transition-duration: 0.01ms !important", block)

    def test_hidden_states_only_apply_once_motion_is_ready(self):
        """With JavaScript off, or motion.js blocked, nothing may stay hidden."""
        css = _strip_keyframes(self._css())
        hidden = [
            selector
            for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
            if re.search(r"opacity:\s*0\s*;", body)
        ]
        self.assertTrue(hidden, "expected at least one hidden-before-reveal rule")
        for selector in hidden:
            for part in selector.split(","):
                with self.subTest(selector=part.strip()):
                    self.assertIn(".motion-ready", part)

    def test_keyframes_animate_only_transform_and_opacity(self):
        frames = re.findall(
            r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", self._css()
        )
        self.assertTrue(frames, "no keyframes found")
        for name, body in frames:
            with self.subTest(keyframes=name):
                self.assertLessEqual(
                    set(re.findall(r"([a-z-]+)\s*:", body)), {"opacity", "transform"}
                )

    def test_motion_flag_is_withdrawn_if_motion_js_never_runs(self):
        theme = (BASE_DIR / "static" / "js" / "theme.js").read_text()
        motion = (BASE_DIR / "static" / "js" / "motion.js").read_text()
        self.assertIn("motion-ready", theme)
        self.assertIn("prefers-reduced-motion: reduce", theme)
        self.assertIn("window.portfolioMotion", theme)
        self.assertIn("window.portfolioMotion = true", motion)

    def test_motion_assets_are_wired_into_every_page(self):
        html = home_html(self.client)
        self.assertIn("css/motion.css", html)
        self.assertIn('js/motion.js" defer', html)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.MotionTest -v 2`
Expected: ERROR/FAIL — `FileNotFoundError` for `motion.css` / `motion.js`, and the flag and wiring assertions fail.

- [ ] **Step 3: Create `static/css/motion.css`**

```css
/* ==========================================================================
   Motion — keyframes, the hero intro and scroll reveals.

   Every "hidden until revealed" state is scoped under .motion-ready, which
   theme.js adds to <html> only when the visitor has not asked for reduced
   motion, and withdraws if motion.js never runs. Without the class —
   JavaScript off, reduced motion, or a failed script — everything renders in
   its final, visible state. Only transform and opacity are animated.
   ========================================================================== */

@keyframes hero-rise {
    from { opacity: 0; transform: translateY(22%); }
    to { opacity: 1; transform: none; }
}

@keyframes portrait-in {
    from { opacity: 0; transform: scale(1.05); }
    to { opacity: 1; transform: none; }
}

@keyframes detect-in {
    from { opacity: 0; transform: scale(1.3); }
    to { opacity: 1; transform: none; }
}

@keyframes fade-up {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: none; }
}

@keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes ticker-scroll {
    to { transform: translateX(-50%); }
}

/* --- Ticker: always moving, paused while hovered --------------------------- */
.ticker-track {
    animation: ticker-scroll 48s linear infinite;
}

.ticker:hover .ticker-track {
    animation-play-state: paused;
}

/* --- Hero intro: about two seconds, once per page load --------------------- */
.motion-ready .hero-word {
    animation: hero-rise var(--dur-slow) var(--ease-out) both;
}

.motion-ready .hero-portrait {
    animation: portrait-in 1000ms var(--ease-out) 250ms both;
}

.motion-ready .hero-detect {
    animation: detect-in 450ms var(--ease-out) 1150ms both;
}

.motion-ready .hero-detect-label {
    animation: fade-in 250ms ease 1450ms both;
}

.motion-ready .hero-intro > *,
.motion-ready .hero-aside > * {
    animation: fade-up 700ms var(--ease-out) both;
}

.motion-ready .hero-intro > :nth-child(1) { animation-delay: 450ms; }
.motion-ready .hero-intro > :nth-child(2) { animation-delay: 530ms; }
.motion-ready .hero-intro > :nth-child(3) { animation-delay: 610ms; }
.motion-ready .hero-intro > :nth-child(4) { animation-delay: 690ms; }
.motion-ready .hero-intro > :nth-child(5) { animation-delay: 770ms; }
.motion-ready .hero-intro > :nth-child(6) { animation-delay: 850ms; }
.motion-ready .hero-aside > :nth-child(1) { animation-delay: 900ms; }
.motion-ready .hero-aside > :nth-child(2) { animation-delay: 1000ms; }

/* --- Scroll reveals ---------------------------------------------------------- */
.motion-ready [data-reveal] {
    opacity: 0;
    transform: translateY(24px);
    transition: opacity 700ms var(--ease-out), transform 700ms var(--ease-out);
    transition-delay: var(--reveal-delay, 0ms);
}

.motion-ready [data-reveal].is-revealed {
    opacity: 1;
    transform: none;
}

/* --- Reduced motion ----------------------------------------------------------- */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }

    .ticker-track {
        width: auto;
        animation: none;
    }

    .ticker-list {
        flex-wrap: wrap;
    }

    .ticker-list[aria-hidden="true"] {
        display: none;
    }
}
```

- [ ] **Step 4: Create `static/js/motion.js`**

```js
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
```

- [ ] **Step 5: Add the motion flag to `static/js/theme.js`**

Inside the IIFE, directly after the line `apply(stored() || DEFAULT_THEME);`, add:

```js

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
```

Also add one sentence to the file's top comment, after "…and it persists.":

```js
 * It also sets the motion flag described below, for the same reason: it has
 * to be in place before the first frame.
```

- [ ] **Step 6: Wire the assets into `templates/base.html`**

Directly below `<link rel="stylesheet" href="{% static 'css/sections.css' %}">` add:

```html
    <link rel="stylesheet" href="{% static 'css/motion.css' %}">
```

Directly below `<script src="{% static 'js/navigation.js' %}" defer></script>` add:

```html
    <script src="{% static 'js/motion.js' %}" defer></script>
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test portfolio.test_redesign.MotionTest -v 2`
Expected: PASS (5 tests).

- [ ] **Step 8: Run the full suite**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test`
Expected: OK — including `ThemeToggleTest` (theme.js still has no `prefers-color-scheme`), `StylesheetHygieneTest` and `StaticAssetTest`.

- [ ] **Step 9: Check the motion in the browser**

With `DEBUG=True venv/Scripts/python.exe manage.py runserver 8000` running, reload `http://127.0.0.1:8000/` at 1440×900. Check: the giant word rises, the portrait fades up, the box lands and its score counts `0.00` → `0.99`, the intro lines and stats stagger in, the stats count up, the ticker scrolls and pauses on hover, sections slide up as they enter, and the portrait and word drift at different speeds while scrolling. With reduced motion emulated (Chrome DevTools → Rendering → `prefers-reduced-motion: reduce`, then reload): nothing moves, the ticker is a static wrapped row, everything is visible. With JavaScript disabled (DevTools → Settings → Debugger → Disable JavaScript, reload): every section is visible.

- [ ] **Step 10: Commit**

```bash
git add static/css/motion.css static/js/motion.js static/js/theme.js templates/base.html portfolio/test_redesign.py
git commit -m "Add hero intro, scroll reveals, count-up and parallax motion"
```

---

### Task 9: Verification, README and pull request

**Files:**
- Modify: `README.md` (Design section, Link Previews section, résumé/identity notes, project structure, tests)

**Interfaces:**
- Consumes: everything above.
- Produces: an updated README and a pushed branch with a pull request.

- [ ] **Step 1: Run the full suite and record the count**

Run: `DEBUG=True venv/Scripts/python.exe manage.py test`
Expected: `OK`. Note the number in the `Ran N tests` line; it goes into the README in Step 6.

- [ ] **Step 2: Visual check, dark theme**

With `DEBUG=True venv/Scripts/python.exe manage.py runserver 8000` running and the local database seeded, check `http://127.0.0.1:8000/` at 1440×900, 1024×768, 768×1024 and 390×844. At every size:
- no horizontal scrollbar;
- the hero's detection box sits on the face;
- the nav is transparent over the hero and becomes a dark bar after scrolling; it hides on scroll down and returns on scroll up;
- below 900 px the menu button opens a full-screen dark overlay with large links, Escape closes it, and the page behind does not scroll;
- the ticker, About, Projects (screenshots zoom with a red wash on hover), Process (red line between icons at ≥900 px), Skills, Journey, Credentials (red quote card), Contact and footer all render with no unstyled elements;
- `/projects/ai-driven-clinical-support-for-hematology-screening/` shows the dark title band with the screenshot overlapping its bottom edge, and the nav links go back to home sections;
- `/does-not-exist/` shows the large red 404.

- [ ] **Step 3: Visual check, light theme**

Click the theme toggle and repeat Step 2 at 1440 and 390. Check: the page turns off-white; the nav, hero and project title band stay dark and readable; red text on the light page is the darker red; the quote card stays deep red with white text; the choice survives a reload.

- [ ] **Step 4: Submit the contact form once locally**

Fill the form with test values (name "Test", email `test@example.com`, subject "Local check", any message) and submit. Expected: redirect back to `#contact` with the green "Your message has been sent successfully." alert, and the close button dismisses it. Submit once with an invalid email: the field shows the red error and the message under it.

- [ ] **Step 5: Lighthouse**

Stop the dev server. Run a production-like server so assets are hashed and compressed:

```bash
venv/Scripts/python.exe manage.py collectstatic --noinput
DEBUG=False SECURE_SSL_REDIRECT=False ALLOWED_HOSTS=127.0.0.1,localhost venv/Scripts/python.exe manage.py runserver 8000 --insecure
```

Run a Lighthouse audit (mobile, navigation mode) on `http://127.0.0.1:8000/` — with the chrome-devtools MCP `lighthouse_audit` tool, or Chrome DevTools → Lighthouse. Expected: Performance ≥ 90 and Accessibility ≥ 90. If Performance is below 90, check that the LCP element is `.hero-portrait` and that it is the 480/768 WebP with `fetchpriority="high"`; if Accessibility is below 90, fix each flagged item (contrast pairs must come from the token table in the spec) and re-run. Stop the server afterwards.

- [ ] **Step 6: Update `README.md`**

Replace the whole `## Design` section (from `## Design` down to, but not including, `## Local Setup`) with:

```markdown
## Design

"Editorial noir": near-black and red, huge condensed display type, and a
spotlight portrait with a computer-vision detection box drawn over the face.
The visual layer is a small, explicit design system rather than a CSS
framework:

| File | Responsibility |
|------|----------------|
| `static/css/variables.css` | **Every colour in the project.** Design tokens for colour, type, spacing, shape, motion and the film-grain texture |
| `static/css/reset.css` | Minimal normalisation |
| `static/css/base.css` | Element typography, page scaffolding, section headings, grain overlay |
| `static/css/components.css` | Header and navigation, buttons, chips, project cards, form, alerts, footer |
| `static/css/sections.css` | Every page section in order — hero, ticker, about, projects, process, skills, journey, credentials, contact — then the project page and the error page, each with its own breakpoints |
| `static/css/motion.css` | Keyframes, the hero intro, scroll reveals and the reduced-motion switch |
| `static/css/responsive.css` | Mobile navigation, page-wide small-screen overrides and print |

The home page is one Django partial per section, in `templates/portfolio/sections/`.

Rules the test suite enforces:

- **Colour lives in one file.** No hex or `rgba()` value may appear outside
  `variables.css`, every `--color-*` token must exist in both themes, and the
  `--color-stage*` tokens must be identical in both.
- **Every stylesheet on disk must be linked.** Orphaned CSS fails the build.
- **No CSS custom properties inside media queries** — `@media (min-width: var(--x))`
  is invalid and silently discards the whole at-rule.
- **Motion is safe by default.** Every hidden-before-reveal state is scoped
  under `.motion-ready`, keyframes animate only `transform` and `opacity`, and
  `prefers-reduced-motion` switches animation off.

Typography is Anton for display type and numbers, Archivo for prose, and IBM
Plex Mono for labels and metadata. Type scales fluidly with `clamp()`, so
there are no per-breakpoint heading overrides.

The red has two values on purpose: `#ef3b42` for red text and `#d61f26` for
button fills. The reference red, `#e5292f`, measures about 4.5:1 against both
black and white — right on the accessibility line — so it is used for neither.

### Theming

Dark is the default for every visitor. The operating-system preference is
deliberately not followed: the design, and the portrait, are built for black.
The toggle switches to a light "paper" theme and the choice is stored.
`static/js/theme.js` is loaded **synchronously in `<head>`** so the stored
choice applies before first paint.

The navigation, the hero and the project page's title band are "stages": they
stay dark in the light theme and use only the `--color-stage*` and
`--color-on-stage*` tokens.

### Motion

`theme.js` adds `.motion-ready` to `<html>` before first paint unless the
visitor asked for reduced motion; `motion.css` scopes every hidden state under
it. `static/js/motion.js` adds the detection-box counter, scroll reveals, the
stats count-up and the hero parallax. If `motion.js` has not run within three
seconds, `theme.js` withdraws the class, so content can never stay invisible.
With JavaScript off, the page is static and complete.

```

Replace the whole `## Link Previews` section (from `## Link Previews` down to, but not including, `## Environment Variables`) with:

````markdown
## Images

```bash
python manage.py make_portrait design/photos/1000256303.jpg
python manage.py make_og_image --photo design/photos/1000256302.jpg
```

`make_portrait` exports the hero portrait as `static/img/portrait-480.webp`
and `static/img/portrait-768.webp`, the two widths the hero's `srcset` serves.
`make_og_image` renders `static/img/og-image.png` (1200×630) from the site
identity settings, with the headshot and the same detection box on the right,
so the card shared to LinkedIn or Slack cannot drift out of date when the
name, role or tagline changes. The original photos live in `design/`, which is
git-ignored (everything under `static/` is published); only the generated
files are committed.

The `og:image` tags are emitted only when the file actually exists, and always
as absolute URLs — scrapers do not resolve relative ones.

`robots.txt` and `sitemap.xml` are served from the app; the sitemap covers the
home page and every project.

````

In the `### Identity` subsection, replace the sentence beginning "Three of these gate UI:" and its paragraph with:

```markdown
Three of these gate UI: `SITE_AVAILABILITY` set to an empty value hides the
availability marker in the navigation and the contact section, `SITE_PHONE`
set to an empty value drops the phone row from the contact section, and the
résumé button appears only once the file at `RESUME_STATIC_PATH` actually
exists — so the site never ships a download link that 404s.
```

In "Keeping the site, the résumé and LinkedIn in step", replace step 3 with:

```markdown
3. Re-run `python manage.py make_og_image --photo design/photos/1000256302.jpg`.
```

In `## Tests`, replace the paragraph that starts with the test count and its two bullets with (put the number from Step 1 in place of `N`):

```markdown
N tests across three files:

- `portfolio/tests.py` — the feature suite: models, views, form validation,
  and every section's rendering and empty state.
- `portfolio/test_regressions.py` — tests that pin previously-fixed bugs and
  the properties the design system relies on: admin permissions, skill
  grouping, seed idempotency, **constant query counts**, static-asset lints,
  colour-token discipline, crawler endpoints, link-preview tags, theme
  behaviour, nav-anchor resolution, honeypot spam protection, résumé wiring,
  project-image delivery and error pages.
- `portfolio/test_redesign.py` — the editorial noir design: navigation off the
  home page, the hero and its portrait files, the ticker, the process and
  credentials sections, the empty-database page, motion safety, and the
  portrait and link-preview commands.
```

In `## Project Structure`, replace the code block with:

```
Portfolio_Django_/
├── portfolio_project/      # Settings, URLs, WSGI/ASGI, env loader, middleware
├── portfolio/              # The app
│   ├── models.py           # Skill, Project, JourneyEntry, Education,
│   │                       # Certification, ProfessionalSkill, ContactMessage
│   ├── views.py            # home, ProjectDetailView, robots.txt
│   ├── sitemaps.py
│   ├── context_processors.py    # Site identity for every template
│   ├── templatetags/            # handle, ticker_skills filters
│   ├── management/commands/     # populate_portfolio, make_portrait, make_og_image
│   ├── tests.py / test_regressions.py / test_redesign.py
├── templates/              # base, components, portfolio/sections/, pages, 404, 500
├── static/                 # css/, js/, img/, files/
├── media/                  # Admin-uploaded project screenshots
├── design/                 # Original photos and mockups (git-ignored)
└── manage.py
```

- [ ] **Step 7: Commit the README**

```bash
git add README.md
git commit -m "Document the editorial noir design system"
```

- [ ] **Step 8: Push and open the pull request — ask the user first**

Pushing publishes the branch. Ask the user before running:

```bash
git push -u origin redesign-editorial-noir
```

`gh` is not installed on this machine, so give the user the compare link to open the PR themselves: `https://github.com/900Gang/Portfolio_Django_/pull/new/redesign-editorial-noir`, with this description:

```markdown
## Summary
- New "editorial noir" design: near-black and red, Anton/Archivo/IBM Plex Mono, a spotlight portrait with a computer-vision detection box, a skills ticker, numbered project cards, a new "How I build" process section, a red quote card and a redesigned contact block.
- Dark by default for every visitor, with a light "paper" theme on the toggle; the nav, hero and project title band stay dark in both.
- Motion with no library: hero intro, scroll reveals, stats count-up and parallax, all off under reduced motion and safe without JavaScript.
- Home page split into one partial per section; CSS split into components, sections and motion.
- Nav links on the project and 404 pages now lead back to the home sections.
- New `make_portrait` command; `make_og_image` redrawn with the headshot.

No model, view, URL or settings changes. Merging deploys to Render.

## Testing
- `DEBUG=True python manage.py test`: all tests pass.
- Checked at 1440, 1024, 768 and 390 px in both themes, with reduced motion and with JavaScript disabled.
- Lighthouse (mobile): Performance ≥ 90, Accessibility ≥ 90.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

