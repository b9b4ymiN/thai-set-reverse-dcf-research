# Deployment Guide

## Recommendation

Deploy this site with **GitHub Pages**.

This repository already contains a dependency-free static site bundle under `netlify/`, and the current execution environment has authenticated GitHub CLI access but no Netlify, Vercel, or Cloudflare credentials. For this project shape, GitHub Pages is the lowest-friction option that still gives:

- free public hosting
- built-in HTTPS
- acceptable global performance for a static research site
- low maintenance for infrequent updates
- simple versioned publishing through GitHub Actions

Netlify would also work well for this site technically, but it would require separate platform credentials from this shell.

## Production URL

The automated deployment target is:

`https://b9b4ymin.github.io/thai-set-reverse-dcf-research/`

## What deploys

- Source content remains in the repository.
- `scripts/build_netlify_site.py` regenerates the publishable static bundle.
- `.github/workflows/deploy-pages.yml` rebuilds the bundle and deploys `netlify/` to GitHub Pages on every push to `main`.

## Update workflow

1. Edit research documents, figures, or data artifacts in the repository.
2. Rebuild locally if you want to inspect the exact generated site before pushing:

```bash
python scripts/build_netlify_site.py --site-url https://b9b4ymin.github.io/thai-set-reverse-dcf-research
```

3. Push to `main`.
4. GitHub Actions rebuilds and republishes the site automatically.

## Maintenance notes

- No JavaScript framework or package install is required for deployment.
- If you later move to a custom domain, update the site URL used by the builder and configure the domain in GitHub Pages settings.
- If you want richer analytics later, add a privacy-conscious script snippet to the generated HTML or front it with a platform that includes analytics by default.
