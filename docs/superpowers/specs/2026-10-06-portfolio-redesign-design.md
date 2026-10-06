# Portfolio redesign — "Editorial noir" (Direction A)

Date: 2026-10-06
Status: approved in conversation, awaiting written-spec review

## 1. Goal

Replace the visual layer of the portfolio at https://nanomachine.xyz with a
distinctive, editorial, black-and-red design based on the reference the owner
supplied (a web designer's portfolio with a giant display word behind a
portrait, a stats rail, numbered project cards, a process strip, a quote card
and a contact block), adapted to an AI developer.

Audience: recruiters and hiring managers for AI / Python developer roles.

Success means:

- The site reads as a deliberate, premium design, not a template, and the
  first screen communicates "AI developer" within a few seconds.
- Every existing section and every admin-managed piece of content still
  renders. No model or view changes.
- All tests pass (existing tests updated where they encode the old design,
  plus new ones listed in section 9).
- Lighthouse performance and accessibility scores of 90 or above on the home
  page (mobile profile).
- Text contrast meets WCAG AA in both themes.

Out of scope: new content types in the admin, a CMS for the process steps or
the quote, a custom cursor, any JavaScript animation library, changes to
hosting.

## 2. Decisions already made

| Decision | Choice |
|----------|--------|
| Direction | A — editorial noir with a computer-vision detection box on the portrait |
| Hero photo | `design/photos/1000256303.jpg` (black suit, spotlight, 768×1344) |
| Link-preview photo | `design/photos/1000256302.jpg` (headshot, 438×442) |
| Other photos | Not used. The hero portrait is the only photo on the page |
| Theme | Dark by default for every visitor; light "paper" theme only via the toggle, choice persisted |
| Motion | Rich, plain CSS + vanilla JS, no library; all of it disabled under `prefers-reduced-motion` |
| Quote | "A model is only as good as the data it learns from." |
| Process steps | Data → Train → Evaluate → Deploy (template copy) |

## 3. Page structure (home page)

Sections in order. Section numbers in eyebrows run 01–07; the hero and the
ticker are unnumbered.

1. **Navigation.** Left: "ANAND N / AI DEVELOPER" (site owner and role from
   settings). Centre: section links. Right: availability dot (only when
   `SITE_AVAILABILITY` is set) and the theme toggle. Below 900 px the links
   collapse into a full-screen overlay menu opened by the existing toggle
   button. The Journey link is shown only when journey entries exist (current
   behaviour, kept).
2. **Hero** (`#home`).
   - A giant uppercase word, "AI DEVELOPER" (from `SITE_ROLE`), in Anton,
     deep red, spanning the width behind the photo, fading to the background
     colour toward its bottom edge.
   - The portrait, centred slightly right of middle, edges faded into the
     background with a CSS mask so no hard photo edge is visible.
   - A detection box drawn over the face: 1.5 px red outline, thicker corner
     brackets, and a filled red label reading `anand_n · 0.99`. Position is
     expressed in percentages of the photo box so it stays on the face at
     every size. The label is decorative (`aria-hidden="true"`).
   - Left column: "Hello, I'm" (mono, red), name in Anton (`SITE_OWNER`),
     role line (role and tagline), `SITE_DESCRIPTION`, then two buttons:
     "View projects" (filled) and "Download résumé" (outline, only when the
     résumé file exists — current rule).
   - Right column: a one-line statement with a small circled ✦ icon
     ("Turning image data into models that see, classify and detect."), then
     a stats rail of three rows: featured projects, technologies,
     certifications. Values are counted in the template from the objects the
     page already renders (`|length`), as today, so no extra queries.
   - `SITE_CURRENT` ("Currently …") appears under the role line when set.
3. **Skills ticker.** A thin full-width red band under the hero with the
   technologies scrolling horizontally, separated by ✦. Built from the
   `skills` already in context (skills with status "Used in projects" first,
   capped at 16). The list is rendered twice for a seamless loop; the second
   copy is `aria-hidden="true"`. Pauses on hover and under reduced motion
   (static, wrapping row instead).
4. **01 About** (`#about`). Left: the first paragraph of the current About
   copy set large as a statement; the remaining two paragraphs below in body
   size. Right: the three existing highlights (AI and machine learning,
   Python development, real-time and IoT data) as numbered rows.
5. **02 Selected projects** (`#projects`). Section header with a long rule.
   Cards in a two-column grid (one column below 760 px): screenshot (16:9,
   placeholder graphic when `has_image` is false — current rule), large red
   number (01, 02…), title, project type and up to four technology tags, and
   an arrow. Whole card links to the project detail page. Empty state kept.
6. **03 How I build** (`#process`, new). Four steps in a row (2×2 below
   900 px, stacked below 560 px), each with a numbered circle icon, a
   title and one line:
   - Data — "Collect, clean and label image and sensor data."
   - Train — "Build and train models with TensorFlow and Keras."
   - Evaluate — "Measure accuracy, inspect failure cases, iterate."
   - Deploy — "Wrap models in Python pipelines and real-time backends."
   A red connecting line runs between the icons on wide screens.
7. **04 Skills** (`#skills`). Existing grouping by category in the editorial
   order (`SKILL_CATEGORY_DISPLAY_ORDER`, sorted in the view as today). Each
   group: mono heading, chips with the status dot (Learning / Building with /
   Used in projects) and a small legend for the dots. Empty state kept.
8. **05 Journey** (`#journey`). Vertical timeline on a red line; month + year
   dates in mono; entry type as a small tag. Section and nav link hidden when
   there are no entries (current behaviour).
9. **06 Education and credentials** (`#education`, with `#certifications`
   kept as an anchor on the certifications column so existing links still
   resolve). Three columns on wide screens:
   - Education: degree, institution, years (and field when set).
   - Certifications and professional skills: certification list with issuer,
     year and credential link; professional skills as outlined chips.
   - Quote card: deep-red block with a large quotation mark, the quote, and
     the owner's name beneath; a "Let's create something" line linking to
     `#contact`.
   Collapses to one column below 900 px. Empty states kept per list.
10. **07 Contact** (`#contact`). Left: "LET'S WORK TOGETHER" in Anton, one
    line of copy, availability. Middle/right: contact rows with icons —
    email, GitHub, LinkedIn, phone (only when `SITE_PHONE` is set), location
    — then the existing form (name, email, subject, message, honeypot) and
    the success/error messages.
11. **Footer.** Owner, role and location; GitHub, LinkedIn, email and résumé
    links; copyright year; colophon.

Other pages restyled to match: project detail (hero band with the project
number and title over the screenshot, description, technology list, links),
404 and 500.

## 4. Visual system

### Colour tokens

All colours stay in `static/css/variables.css` (the colour lint is kept).
The dark palette is declared on `:root`; the light palette is declared under
`:root[data-theme="light"]`. Every `--color-*` token must exist in both.

| Token | Dark | Light | Use |
|-------|------|-------|-----|
| `--color-bg` | `#070707` | `#f4f1ec` | Page |
| `--color-surface` | `#0f0f0f` | `#ffffff` | Cards |
| `--color-surface-raised` | `#151515` | `#ebe6df` | Chips, inputs |
| `--color-text-primary` | `#f2efea` | `#111111` | Body |
| `--color-text-secondary` | `#b9b3ad` | `#4a4540` | Supporting copy |
| `--color-text-muted` | `#8a847e` | `#6b655f` | Labels, metadata |
| `--color-border` | `#262626` | `#d9d2c8` | Hairlines |
| `--color-accent` | `#ef3b42` | `#b3141b` | Red text, links, icons |
| `--color-accent-fill` | `#d61f26` | `#b3141b` | Button backgrounds |
| `--color-on-accent` | `#ffffff` | `#ffffff` | Text on red fills |
| `--color-accent-deep` | `#c8161d` | `#c8161d` | Giant hero word, quote card |
| `--color-stage` | `#070707` | `#070707` | Hero and quote card backgrounds in both themes |
| `--color-on-stage` | `#f2efea` | `#f2efea` | Text on the stage in both themes |

Plus the existing semantic tokens (success, error, warning) re-tuned for both
grounds, and alpha tokens for the grain overlay, the photo mask and the nav
backdrop.

Contrast checks (AA requires 4.5:1 for body text):

- `#8a847e` on `#070707` ≈ 5.4:1; `#ef3b42` on `#070707` ≈ 5.2:1.
- White on `#d61f26` ≈ 5.1:1; white on `#c8161d` ≈ 5.9:1; white on `#b3141b` ≈ 6.9:1.
- On raised surfaces: `#ef3b42` on `#0f0f0f` ≈ 4.9:1; `#8a847e` on `#151515` ≈ 4.9:1.
- `#b3141b` on `#f4f1ec` ≈ 6.1:1; `#6b655f` on `#f4f1ec` ≈ 5.1:1.

The plain reference red `#e5292f` is not used for text or button fills: it
measures about 4.5:1 against black and white, which is too close to the line.

The hero and the quote card always use the stage colours, so in the light
theme they remain dark panels. The portrait only works on black.

### Theme behaviour

- No stored choice: dark.
- Toggle switches between dark and light and stores the choice in
  `localStorage`; `theme.js` stays synchronous in `<head>` so the stored theme
  applies before first paint.
- The OS colour-scheme preference is intentionally not followed (dark is the
  brand look). `color-scheme` is set per theme so form controls and
  scrollbars match.

### Typography

- Display: **Anton** (headlines, section titles, hero word, numbers, stats).
  Fallback stack: `"Anton", "Impact", "Haettenschweiler", "Arial Narrow Bold", system-ui, sans-serif`.
- Body: **Archivo** 400/500/600. Fallback: `"Archivo", system-ui, -apple-system, "Segoe UI", sans-serif`.
- Labels and metadata: **IBM Plex Mono** 400/500 (kept). Fallback:
  `"IBM Plex Mono", ui-monospace, "SFMono-Regular", Consolas, monospace`.
- Loaded from Google Fonts in one `<link>` with `display=swap`; the existing
  preconnects are kept.
- Sizes are fluid with `clamp()`. Display headings are uppercase with slight
  positive tracking; body text stays sentence case. Display line-height is at
  least 0.92 (tighter values overlap Anton's glyphs on wrap).

### Texture

A full-page film-grain overlay: an inline SVG `feTurbulence` noise as a CSS
background on a fixed, `pointer-events: none` pseudo-element at very low
opacity. No network request. Hidden in print.

## 5. Motion

Implemented in `static/css/motion.css` and `static/js/motion.js`. Progressive
enhancement: `motion.js` adds a `motion-ready` class to `<html>`; every
"hidden before reveal" state is scoped under `.motion-ready`, so with
JavaScript off all content is visible and static. Under
`prefers-reduced-motion: reduce` the script does nothing and the CSS block
disables animations and transitions.

- **Hero intro** (about 2 s, once per page load):
  1. Giant word rises into place with a clip reveal (0–0.8 s).
  2. Portrait fades up from black with a slight scale (0.3–1.2 s).
  3. Detection box draws its corners, then the label appears and its
     confidence counts from `0.00` to `0.99` (1.2–2.0 s).
  4. "Hello, I'm", name, role, description, buttons and stats fade up in a
     stagger.
- **Scroll reveals:** section heads and cards slide up 24 px and fade in when
  they enter the viewport (IntersectionObserver), staggered within a group.
- **Stats count-up:** the three stats count up from 0 the first time they are
  visible.
- **Parallax:** on wide screens, the portrait and the giant word translate at
  different rates while the hero is in view (`transform` only, one
  `requestAnimationFrame` loop, stops when the hero is off screen).
- **Ticker:** CSS keyframe marquee, paused on hover and focus.
- **Project cards:** on hover/focus, screenshot scales to 1.04 under a red
  wash and the arrow slides right.
- **Navigation:** hides when scrolling down past the hero, reappears when
  scrolling up; active section highlighted (existing behaviour kept).

Only `transform` and `opacity` are animated.

## 6. Code structure

### Stylesheets (`static/css/`)

| File | Contents |
|------|----------|
| `variables.css` | Rewritten: colour, type, spacing, radius and motion tokens; dark on `:root`, light under `[data-theme="light"]` |
| `reset.css` | Kept |
| `base.css` | Rewritten: element typography, links, forms, page scaffolding, grain overlay |
| `components.css` | Rewritten and reduced: nav, buttons, chips, cards, form fields, footer |
| `sections.css` | New: hero, ticker, about, projects, process, skills, journey, credentials, contact, project detail, error pages |
| `motion.css` | New: keyframes, `.motion-ready` reveal states, reduced-motion block |
| `responsive.css` | Rewritten: breakpoints at 1100, 900, 760 and 560 px, mobile menu, print |

All are linked from `base.html` in that order. Rules the tests already
enforce stay: no colour literals outside `variables.css`, no `var()` inside
media-query conditions, no orphaned stylesheets.

### Templates (`templates/`)

- `base.html`: font link, theme script in `<head>`, stylesheets, skip link,
  `navigation.js` and `motion.js` with `defer`.
- `portfolio/home.html` becomes a thin page that includes one partial per
  section from `portfolio/sections/`: `hero.html`, `ticker.html`,
  `about.html`, `projects.html`, `process.html`, `skills.html`,
  `journey.html`, `credentials.html`, `contact.html`.
- Restyled: `components/navigation.html`, `components/footer.html`,
  `components/project_card.html`, `components/form_field.html`,
  `portfolio/project_detail.html`, `404.html`, `500.html`.

### JavaScript (`static/js/`)

- `theme.js`: dark default, toggle, persistence, no flash.
- `navigation.js`: mobile menu, active-section highlight (kept), plus
  hide-on-scroll.
- `motion.js` (new): hero intro, confidence counter, reveals, count-up,
  parallax. No dependencies.

### Images

- Hero portrait exported with Pillow to `static/img/portrait-480.webp` and
  `static/img/portrait-768.webp` (quality about 82), referenced with
  `srcset`/`sizes`, explicit `width`/`height`, `fetchpriority="high"` and no
  lazy loading (it is the largest contentful element).
- `make_og_image` redrawn in the new palette: black ground, the headshot on
  the right, name in a condensed display face and role in red. The command
  looks for Anton first and falls back to Impact (present on Windows), then
  Arial Black. The PNG is generated locally and committed, as today.
- `design/` (original photos and mockups) and `.claude/` are added to
  `.gitignore`.

### Data

No model, migration, view or URL changes. The process steps and the quote
live in their section templates.

## 7. Accessibility

- Skip link, landmarks and `aria-label`s kept.
- Visible focus rings on every interactive element, in the accent colour.
- Detection box, grain and ticker duplicate are `aria-hidden`; the portrait
  has descriptive alt text ("Portrait of Anand N").
- Heading order: one `h1` (name), `h2` per section, `h3` inside.
- Reduced motion fully respected (section 5).
- External links keep the "(opens in a new tab)" announcement.

## 8. Performance

- One portrait request at an appropriate width (WebP, about 40–80 KB).
- Fonts: three families, five weights total, `display=swap`.
- No new third-party scripts. `motion.js` is small and deferred.
- Static assets keep WhiteNoise hashing and long-lived caching.

## 9. Testing

Update (they encode the old design):

- `ThemeTokenTest`: replace the dark-mode-block checks with "every
  `--color-*` token is defined on `:root` and under `[data-theme="light"]`";
  font checks move from IBM Plex Sans to Anton and Archivo (IBM Plex Mono
  stays); the Bootstrap-palette check stays.
- `ThemeTokenTest.test_stylesheet_link_for_the_webfont_is_present`: expects
  Anton and Archivo in the Google Fonts URL.
- `NavigationWiringTest`: includes the new `#process` anchor.
- `ThemeToggleTest`: still requires the toggle and the synchronous theme
  script; adds a check that the script defaults to dark.

Add:

- The hero portrait files exist in the static tree and the home page renders
  them with `srcset`.
- The quote and the four process steps render on the home page.
- `motion.css` contains a `prefers-reduced-motion: reduce` block, and no
  reveal state applies without `.motion-ready`.
- Every stylesheet linked in `base.html` exists (existing) and the new files
  are linked (covered by the orphan test).

Keep unchanged: query-count tests, empty-state tests, honeypot, résumé
wiring, link preview, crawler endpoints, error pages, image fallback.

Manual verification before the PR:

- Browser check at 1440, 1024, 768 and 390 px, in both themes, with and
  without reduced motion, and with JavaScript disabled.
- Lighthouse (mobile) on the home page: performance and accessibility 90+.

## 10. Delivery

Work on a feature branch; open a PR; merging to `main` deploys to Render.
The README's Design section is updated to describe the new system.
