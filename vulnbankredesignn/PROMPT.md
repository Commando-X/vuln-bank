# Frontend Update — All Changes

Replace the files listed below with the versions from `vuln-bank-redesign/`. This covers the color swap from lime to blue, theme toggle visibility fix, tighter landing page spacing, new landing page sections, legal pages, and API docs link.

## Files to replace in `static/`

- `style.css` — Updated design tokens: accent is now `#007BFF` (not lime), added `--brand-light: #3D9BFF` and `--brand-dark: #0062CC`, sidebar bg is `#0C2A50`, glow shadows use blue `rgba(0,123,255,...)`, dark mode buttons use `--brand-light` with white text. Theme toggle now has a visible border (`border: 1px solid var(--border)`) and uses `color: var(--text-2)` so icons are visible in both modes.
- `auth.css` — Brand panel radial uses `rgba(0,123,255,0.08)`, logo icon uses `var(--brand)` with white svg.
- `dashboard.css` — All lime references replaced with blue equivalents. Sidebar logo/active indicator use brand blue. Action pill hover uses brand blue border. Chat status dot is green (not accent). Dark mode chat/send buttons use brand blue.
- `admin.css` — Header radial uses `rgba(0,123,255,0.06)`.

## Files to replace in `templates/`

- `index.html` — Complete rewrite of the landing page with:
  - Tighter spacing: hero padding reduced to `4.5rem` top / `2rem` bottom, `min-height: calc(100vh - 4rem)` instead of `100vh`, features `4rem/3rem`, CTA `3rem/3rem`
  - Stats moved out of hero into a dedicated **social proof strip** section below the hero (50K+, $1.8B, 99.9%, 24/7)
  - New **"How it works"** section with 3 numbered steps connected by a dashed line
  - New **dashboard preview** section with a static HTML/CSS mockup (mini sidebar + fake cards + fake transaction rows)
  - API Docs link in footer points to `/static/openapi.json`
  - Legal links use `url_for('privacy')`, `url_for('terms')`, `url_for('compliance')`
  - Theme toggle has `style="color: var(--text-2);"` for visibility
  - All colors are blue-based, no lime anywhere

- `login.html`, `register.html`, `forgot_password.html`, `reset_password.html` — Unchanged from last deploy (already have theme init script).

- `dashboard.html` — Unchanged from last deploy (lime inline button on "View Cards" was already updated to blue in a previous prompt).

- `admin.html` — Unchanged from last deploy.

## New files to add to `templates/`

- `privacy.html` — Cheeky privacy policy page joking about plaintext passwords, IDOR, SSRF, and data handling.
- `terms.html` — Tongue-in-cheek terms of service about localStorage tokens, no CSRF, XSS as a feature, no rate limiting.
- `compliance.html` — Mock compliance page with "Non-Compliant" certification cards for OWASP Top 10, PCI DSS, GDPR, and SOC 2. References specific vulns in the app.

All three pages use `style.css`, include the theme toggle, and link back to the landing page.

## Routes to add in `app.py`

Add these three routes (place them near the other page routes, e.g. after the `index` route):

```python
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/compliance')
def compliance():
    return render_template('compliance.html')
```

## What NOT to change

- `dashboard.js` — untouched
- `auth.py`, `database.py` — untouched
- `favicon.svg`, `favicon-16.svg`, `user.png`, `openapi.json`, `uploads/` — untouched
- All intentional vulnerabilities — preserved
- All element IDs, form IDs, Jinja2 variables — preserved
