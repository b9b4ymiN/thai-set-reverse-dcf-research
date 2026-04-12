# Netlify Site Bundle

This directory contains a static documentation site for the Thai SET reverse DCF project.

## What is included

- `index.html` landing page
- `guide/index.html` Thai reader-first guide
- `thesis.html` generated thesis page
- `research/index.html` methodology and datasource notes
- `backtest/index.html` results dashboard with local figures
- `about/index.html` project overview
- `download/index.html` document and data downloads
- `css/style.css` shared styling
- `assets/` local copies of documents, figures, and CSV extracts
- `sitemap.xml` and `robots.txt`

## Rebuild

From the repository root:

```bash
python scripts/build_netlify_site.py --site-url https://rdcf.netlify.app
```

If you know the production URL, replace the example value above before deployment so `sitemap.xml` and `robots.txt` use the correct base URL.

## Deploy to Netlify

1. Set the publish directory to `netlify/`.
2. No build command is required if the generated files are already committed.
3. If you want Netlify to rebuild the site during deploy, use:

```bash
python scripts/build_netlify_site.py --site-url "$URL"
```

## Deploy to GitHub Pages

1. Publish the `netlify/` directory via the Pages workflow or a `gh-pages` branch.
2. If the site will be served from a subpath, rebuild with the final absolute site URL first.

## Notes

- The site is dependency-free HTML and CSS.
- Asset copies are intentionally local for fast loading and portability.
- The thesis conversion is produced from `docs/thesis_reverse_dcf_thai_set.md`.
