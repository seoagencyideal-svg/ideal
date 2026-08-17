# Permanent Client Website Deployment

The Local Business Engine now publishes generated client websites into `public/sites/<slug>/index.html` in this repository. GitHub Pages deploys the `public/` directory after pushes to `main`.

## Required server environment variables

```env
GITHUB_TOKEN=your_github_token
GITHUB_REPO_OWNER=seoagencyideal-svg
GITHUB_REPO_NAME=ideal
GITHUB_BRANCH=main
GITHUB_PAGES_BASE_URL=https://seoagencyideal-svg.github.io/ideal
```

`GITHUB_TOKEN` must have permission to write repository contents.

## One-time GitHub Pages setup

In the repository settings, open **Pages** and set **Build and deployment → Source** to **GitHub Actions**.

The repository is public, so GitHub Pages is available on GitHub Free.

## Deployment flow

1. Lead Finder finds a no-website business.
2. The selected lead carries Google Places business data and available Google business photos.
3. Demo Builder generates the client-specific brief.
4. **Build & Deploy Website** calls `/api/deploy`.
5. The backend creates/updates `public/sites/<slug>/index.html` through the GitHub Contents API.
6. The Pages workflow publishes the `public/` directory.
7. The permanent URL is `https://seoagencyideal-svg.github.io/ideal/sites/<slug>/` unless `GITHUB_PAGES_BASE_URL` is changed.

## Important limitation

The generated sites are static. This is intentional for reliability and low hosting overhead. Client-specific forms, dashboards, or server-side features should be added later with a separate backend/API rather than embedded secrets in the public site.
