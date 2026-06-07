# Venter Field Notes

An Astro + TypeScript + Tailwind CSS personal site shaped as a portfolio, notebook, and archive. It uses Markdown content collections, static output, SEO metadata, RSS, sitemap generation, dynamic SVG Open Graph images, client-side search, and lightweight theme/language toggles.

The current design direction is **Warm Archive Garden**: soft paper backgrounds, low-saturation gray, deep brown-gray, dark gold accents, light archive labels, and a medium-low density homepage. [src/layouts/BaseLayout.astro](src/layouts/BaseLayout.astro) loads Newsreader, Inter, and JetBrains Mono; [src/styles/global.css](src/styles/global.css) exposes the color tokens to Tailwind.

## Local Setup

The requested conda environment is `psblog` with Python 3.11. It is reserved for future content tooling and migration scripts.

```powershell
conda run -n psblog python --version
```

`pnpm` was not available on this machine during initialization, so use `npm` unless you install `pnpm` later.

The project pins Astro 4.16.19 because this machine currently uses Node.js 18.19.0. Upgrade Node to 18.20.8 or newer before moving to Astro 5.

```powershell
npm install
npm run dev
```

Build the production site with:

```powershell
npm run build
```

Preview the generated output with:

```powershell
npm run preview
```

## Content

- Blog posts live in [src/content/blog](src/content/blog) and render under `/blog/[slug]/`.
- Pages live in [src/content/pages](src/content/pages) and render under `/pages/[slug]/`.
- Public shelves are available at `/notes/`, `/essays/`, `/projects/`, `/atlas/`, and `/archive/`.
- `/notes/` and `/blog/` currently read from the same blog collection; `/essays/` filters writing/essay tags and falls back to all posts until a dedicated essay model is added.
- `/projects/` and `/atlas/` are planned portfolio/observation shelves with placeholder pages, not new content collections yet.
- Frontmatter schemas are defined in [src/content/config.ts](src/content/config.ts).
- Content helpers and exported types live in [src/utils/content.ts](src/utils/content.ts).

## Interface Language

The language toggle only changes interface labels such as navigation, index entries, buttons, and search status text. It does not translate authored content or create localized routes. The browser preference is stored in `localStorage` under `psblog-locale`, defaulting to English.

## GitHub Pages

The current public URL is configured for the `VenterWu` GitHub Pages user site:

```ts
site: 'https://VenterWu.github.io'
base: '/'
```

Before deploying, update [src/utils/config.ts](src/utils/config.ts):

- For a user or organization site, keep `base` as `/`.
- For a project repository, set `base` to `/<repo-name>`.

[public/robots.txt](public/robots.txt) should use the same public URL for the sitemap.

Deployment is configured in [.github/workflows/deploy.yml](.github/workflows/deploy.yml) using Astro's official `withastro/action` and `actions/deploy-pages`. In GitHub repository settings, set Pages source to GitHub Actions.

## Migration Notes

When moving posts from another blog:

1. Convert Markdown frontmatter to the schema in [docs/content-schema.md](docs/content-schema.md).
2. Put posts in [src/content/blog](src/content/blog) and stable pages in [src/content/pages](src/content/pages).
3. Update internal links and image paths.
4. Run `npm run build` to validate routes, content schema, RSS, and sitemap generation.
5. Add redirects separately if old URLs need to stay reachable.

## Documentation Index

- [docs/architecture.md](docs/architecture.md): project structure, route map, build and deployment design.
- [docs/content-schema.md](docs/content-schema.md): collection schemas, examples, and migration rules.
- [docs/dev-guide.md](docs/dev-guide.md): environment, install, run, build, deploy, and troubleshooting steps.
- [docs/agile.md](docs/agile.md): MVP definition, backlog, done criteria, and release risks.
