# Development Guide

## Environment

The local Python environment is named `psblog` and must use Python 3.11. It is available for future content tooling, image scripts, or migration scripts, although the Astro MVP itself runs on Node.js.

Validate it with:

```powershell
conda run -n psblog python --version
```

Node.js is required for Astro. This workspace currently reports Node.js 18.19.0, so the project pins Astro to 4.16.19. Upgrade Node to 18.20.8 or newer before moving to Astro 5.

`pnpm` is preferred by the original task, but this machine currently does not expose `pnpm` in PATH. Use `npm` unless `pnpm` is installed later.

## Install

Preferred when `pnpm` is available:

```powershell
pnpm install
```

Current fallback:

```powershell
npm install
```

## Run Locally

```powershell
npm run dev
```

Astro prints the local URL, usually `http://localhost:4321/`.

## Build

```powershell
npm run build
```

The build runs Astro type/content checks and writes static output to `dist/`.

## Preview

```powershell
npm run preview
```

Use this after `npm run build` to inspect the production output locally.

## GitHub Pages Configuration

The current config uses:

```ts
site: 'https://VenterWu.github.io'
base: '/'
```

For a user or organization Pages site, keep `base` as `/`.

For a project repository, set `base` to `/<repo-name>` in `src/utils/config.ts`; `astro.config.ts` reads the exported config directly.

## Deployment

1. Push to the trigger branch configured in `.github/workflows/deploy.yml`, default `main`.
2. In the repository settings, set Pages source to GitHub Actions.
3. Confirm `site.url`, `site.base`, and `public/robots.txt` match the final public URL before deployment.
4. Confirm the Actions run completes and publishes the `github-pages` environment.

## Add A Blog Post

1. Create `src/content/blog/my-post.md`.
2. Add frontmatter that satisfies `docs/content-schema.md`.
3. Write Markdown content with headings for the TOC.
4. Run `npm run build`.

## Add A Page

1. Create `src/content/pages/my-page.md`.
2. Add title, description, and optional order.
3. The page appears at `/pages/my-page/`.
4. Add a navigation item in `src/utils/config.ts` if it should be globally visible.

## Add Or Update A Shelf Route

The current top-level shelves are `/notes/`, `/essays/`, `/projects/`, `/atlas/`, and `/archive/`.

- Keep route constants in `src/utils/config.ts` and use `withBase()` for links.
- `/notes/` and `/blog/` currently read from `src/content/blog`.
- `/essays/` filters writing/essay tags and falls back to all posts.
- `/projects/` and `/atlas/` are placeholder Astro pages until dedicated content collections are added.
- `/archive/` is generated from published blog posts and tag stats.
- Run `npm run build` after adding any route so Astro, RSS, sitemap, and search stay valid.

## Interface Language Labels

Use `data-i18n="key"` on navigation, index, and button labels that should switch between English and Chinese. Add the matching key to `src/components/LanguageToggle.astro`. Use `data-i18n-placeholder="key"` for input placeholders. Do not translate Markdown content through this toggle.

## Customize Styling

- Global tokens and base styles live in `src/styles/global.css`.
- Tailwind content scanning is configured in `tailwind.config.mjs`.
- Keep theme colors defined through CSS variables so dark mode stays consistent.
- Warm Archive Garden uses Newsreader for display/headings, Inter for UI/body, and JetBrains Mono for labels.
- Keep the visual language soft: paper backgrounds, light borders, dark gold accents, small archive labels, and subtle hover motion.

## Troubleshooting

- Schema error: check frontmatter types and required fields.
- Broken GitHub Pages paths: verify `siteConfig.site.base`.
- Missing RSS or sitemap URLs: verify `siteConfig.site.url` is no longer the placeholder before deployment.
- Search returns nothing: ensure content is not marked `draft: true` and rebuild.
- Unsupported Astro engine: either keep the pinned Astro 4 versions or upgrade Node before changing dependency ranges.
- Audit remediation: `npm audit --omit=dev` recommends a breaking Astro 6 upgrade. Upgrade Node first, then run Astro's official upgrade flow and rebuild.