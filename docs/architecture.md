# Architecture

## Goal

This project is an Astro personal blog MVP focused on static output, small client-side JavaScript, and content that can be edited through Markdown. The first deploy target is GitHub Pages.

## Stack

- Astro 4.16.19 with TypeScript for routing, layouts, and static generation. The version is pinned because the current local Node.js version is 18.19.0; Astro 5 requires Node 18.20.8 or newer.
- Astro Content Collections for typed `blog` and `pages` entries.
- Markdown for authored content.
- Tailwind CSS for styling through Astro's Tailwind integration. The current visual system is Warm Archive Garden: portfolio, notebook, and archive with a soft paper feel.
- Small vanilla JavaScript only for theme switching, UI-only language switching, and search.
- `@astrojs/rss` for RSS and `@astrojs/sitemap` for sitemap generation.

No React, Vue, or Svelte islands are planned for the MVP. If interactive features become complex later, prefer a plain custom element first, then consider an island framework only after documenting the trade-off.

## Visual System

The site uses a three-font pairing loaded in `src/layouts/BaseLayout.astro`: Newsreader for the motto, article headings, and archive display type; Inter for interface and body text; JetBrains Mono for index labels, dates, metadata, and compact navigation.

Design tokens live in `src/styles/global.css` and are exposed to Tailwind in `tailwind.config.mjs`. The light theme uses warm white paper, low-saturation gray, deep brown-gray ink, and dark gold accents. The dark theme keeps the same archival palette in lower light. Both themes use the same variable names so component classes stay stable.

The Warm Archive Garden language is implemented with soft paper backgrounds, light borders, small gold details, rounded archive panels, minimal hover movement, and medium-low information density. The previous visible grid, signal-red blocks, hard shadows, and industrial composition have been removed. Key implementation points are `BaseLayout.astro` for font loading and background structure, `Header.astro`/`Footer.astro` for global chrome, `PostCard.astro`, `TagList.astro`, `SearchBox.astro`, and `src/pages/index.astro` for the homepage motto, left index, right content stream, and Atlas/Projects previews.

## UI Language Strategy

The site supports an interface-only language toggle through `src/components/LanguageToggle.astro`. It stores the selected locale in `localStorage` as `psblog-locale` and updates elements marked with `data-i18n` or `data-i18n-placeholder`. The default locale is English. Chinese mode changes navigation, index labels, buttons, theme labels, and search status text only; authored Markdown content remains in its original language and no i18n routes are generated.

## Site Configuration

All replaceable site settings live in `src/utils/config.ts`:

- `site.url`: currently `https://VenterWu.github.io`.
- `site.base`: default `/`.
- title, description, author, locale, social metadata, default image, navigation links, and footer links.
- top-level navigation for Notes, Essays, Projects, Atlas, Archive, and About.

For a GitHub Pages project repository, change `site.base` to `/<repo-name>` and set `site.url` to the account or organization Pages URL. Keep route generation and canonical URL helpers reading from this central config.

## Main Routes

- `/`: motto hero with avatar placeholder, expandable motto history, left index, latest/featured posts, topic map, search, and Atlas/Projects previews.
- `/notes/`: notebook-style list of all published blog posts.
- `/blog/`: legacy list of all published blog posts, kept for existing post URLs and helpers.
- `/blog/[slug]/`: blog article page with SEO, reading time, tags, table of contents, and previous/next navigation.
- `/essays/`: writing/essay-tagged post shelf, with a fallback to all posts until a dedicated collection exists.
- `/projects/`: placeholder portfolio shelf for small tools, prototypes, and experiments.
- `/atlas/`: placeholder shelf for travel, life photos, and place observations.
- `/archive/`: chronological archive of published notes with a topic map.
- `/tags/[tag]/`: posts filtered by tag.
- `/pages/[slug]/`: authored static pages such as About.
- `/rss.xml`: RSS feed generated at build time.
- `/search.json`: static search index generated from published blog posts and pages.
- `/og/[slug].svg`: SVG-backed dynamic OG image endpoint for posts and pages. This keeps the MVP dependency-light; it can be replaced by a PNG renderer later if a social platform requires raster OG images.

## Component Boundaries

- `src/layouts/BaseLayout.astro`: document shell, global header/footer, theme boot script, SEO composition.
- `src/layouts/PostLayout.astro`: article shell for blog posts, TOC, metadata, prev/next navigation.
- `src/layouts/PageLayout.astro`: shell for normal content pages.
- `src/components/SEOHead.astro`: meta, canonical, Open Graph, and Twitter tags.
- `src/components/Header.astro` and `Footer.astro`: site navigation and global chrome.
- `src/components/LanguageToggle.astro`: UI-only locale toggle using vanilla JavaScript and `localStorage`.
- `src/components/PostCard.astro`: reusable post summary card.
- `src/components/TagList.astro`: tag rendering and links.
- `src/components/SearchBox.astro`: client-side search UI backed by `/search.json`.
- `src/components/ThemeToggle.astro`: vanilla JavaScript theme switcher.

## Content Flow

1. Authors add Markdown files under `src/content/blog` or `src/content/pages`.
2. `src/content/config.ts` validates frontmatter with Zod.
3. `src/utils/content.ts` reads collections, filters drafts, sorts posts, computes tags, and builds search/SEO data.
4. Pages call those utilities and render typed data.
5. Build emits static HTML, RSS, sitemap, OG images, and search JSON.

## Build And Deployment

The project builds to static files in `dist/`. GitHub Actions uses Astro's official `withastro/action` followed by `actions/deploy-pages`. The workflow keeps comments around permissions, branch triggers, and public site environment values so deployment changes are easy to audit.

## Extension Points

- Add a content collection for projects, atlas entries, notes, or changelogs in `src/content/config.ts` when placeholders need typed data.
- Add navigation links in `src/utils/config.ts` only.
- Add SEO defaults in `siteConfig.seo` and keep page-level overrides passed through layouts.
- Extend search by adding fields to `createSearchDocument` in `src/utils/content.ts`.
- Replace the OG endpoint implementation without changing callers because pages only generate URLs through `getOgImageUrl`.
- Extend Atlas with image metadata, place names, dates, and optional coordinates when the content model is ready.
- Extend Projects with status, stack, repository/demo links, and case-study body content when portfolio entries become real content.

## Quality Gates

- `npm install` when `pnpm` is unavailable.
- `npm run build` must pass before deployment.
- New content must satisfy collection schema validation.
- New public routes must have SEO metadata and be reachable from navigation or content links.
- Interface language changes must remain UI-only unless a full i18n routing strategy is documented first.