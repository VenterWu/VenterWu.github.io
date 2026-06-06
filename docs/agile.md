# Agile Plan

## MVP Definition

The MVP is complete when a reader can browse posts, open an article, filter by tag, search content, switch theme, subscribe to RSS, and deploy the static site to GitHub Pages.

## Current Sprint Scope

- Initialize Astro, TypeScript, Tailwind, RSS, and sitemap.
- Add typed blog and page content collections.
- Implement core layouts and components.
- Add sample content.
- Add GitHub Pages workflow.
- Verify dependency installation and production build.

## Backlog

| ID | Type | Goal | Acceptance Criteria | Priority |
| --- | --- | --- | --- | --- |
| BL-001 | Feature | Publish typed blog posts | At least two Markdown posts render under `/blog/` and individual routes pass schema validation. | P0 |
| BL-002 | Feature | Publish typed pages | `about.md` renders under `/pages/about/` with page layout and SEO metadata. | P0 |
| BL-003 | Feature | Centralize site settings | URL, base path, author, nav, and social links are editable in `src/utils/config.ts`. | P0 |
| BL-004 | Feature | SEO metadata | Home, list, tag, post, and page routes include title, description, canonical, OG, and Twitter tags. | P0 |
| BL-005 | Feature | RSS feed | `/rss.xml` contains all non-draft posts with correct titles, descriptions, dates, and links. | P0 |
| BL-006 | Feature | Sitemap | Production build emits sitemap using the configured site URL. | P0 |
| BL-007 | Feature | Dynamic OG images | Posts and pages can reference generated `/og/[slug].svg` images. | P1 |
| BL-008 | Feature | Client search | `/search.json` is generated and the search UI filters posts/pages without a framework island. | P1 |
| BL-009 | Feature | Theme switching | Theme toggle persists light/dark preference and avoids flash through an early inline script. | P1 |
| BL-010 | Feature | Article navigation | Blog posts show reading time, TOC, tags, and previous/next links. | P1 |
| BL-011 | Chore | GitHub Pages deployment | Workflow uses `withastro/action` and `actions/deploy-pages` with documented permissions and branch trigger. | P1 |
| BL-012 | Documentation | Developer onboarding | README and docs explain install, local run, build, deployment, migration, and content schema. | P1 |
| BL-013 | Enhancement | Projects collection | Add a typed `projects` collection and `/projects/` route after the blog MVP stabilizes. | P2 |
| BL-014 | Enhancement | Content migration script | Use the `psblog` Python environment for scripts that normalize imported Markdown frontmatter. | P2 |

## Done Criteria

- Documentation exists before code and is synchronized after implementation.
- `npm install` succeeds when `pnpm` is unavailable.
- `npm run build` succeeds.
- No UI island framework is added.
- Placeholder GitHub Pages values are isolated and documented.
- Astro dependency versions remain compatible with the local Node runtime, or the Node upgrade is documented before changing versions.

## Release Risks

- `site.url` and `site.base` must be replaced before public deployment.
- RSS and sitemap correctness depend on the final GitHub Pages URL.
- Search is static and requires a rebuild after content changes.
- `npm audit --omit=dev` currently reports Astro/Vite/esbuild advisories. The npm-suggested fix upgrades to Astro 6, so plan a Node upgrade before taking that remediation path.