# Content Schema

## Collections

The MVP uses Astro Content Collections in `src/content/config.ts`.

### `blog`

Purpose: long-form posts shown in lists, tags, RSS, sitemap, search, and article pages.

Required frontmatter:

- `title`: string, readable post title.
- `description`: string, 20 to 180 characters, used for SEO and cards.
- `pubDate`: date, first publication date.
- `author`: string, defaults should match `siteConfig.author.name` in examples.
- `tags`: array of strings, at least one tag.

Optional frontmatter:

- `updatedDate`: date, when material changes happen.
- `heroImage`: string path or URL used for SEO image fallback.
- `draft`: boolean, default `false`; drafts are excluded from public lists and feeds.
- `featured`: boolean, default `false`; featured posts can be highlighted on the home page.

Content expectations:

- Start with an `h2` or lower heading after frontmatter; the page layout owns the `h1`.
- Use semantic Markdown headings because the TOC is derived from rendered headings.
- Keep tags stable and lowercase where possible, for example `astro`, `typescript`, `writing`.

Example:

```md
---
title: Building A Calm Personal Site
description: A practical note on shaping a personal site around writing and small tools.
pubDate: 2026-06-06
author: Kefan Wu
tags: [astro, writing]
featured: true
---

## Why Start Small

Content goes here.
```

### `pages`

Purpose: stable Markdown pages such as About, Now, Uses, or Colophon.

Required frontmatter:

- `title`: string.
- `description`: string, 20 to 180 characters.

Optional frontmatter:

- `updatedDate`: date.
- `order`: number for manual page ordering.
- `draft`: boolean, default `false`.

Example:

```md
---
title: About
description: A short introduction to the author and this site.
order: 1
---

## Hello

Content goes here.
```

## Exported Types

`src/content/config.ts` exports schema through Astro's collection definitions. Use `CollectionEntry<'blog'>` and `CollectionEntry<'pages'>` in utilities and components when typed entries are needed.

Project helper types are exposed from `src/utils/content.ts`:

- `PublishedBlogPost`: non-draft blog entry used in lists, tags, RSS, SEO, and navigation.
- `PublishedPage`: non-draft page entry used in page routes and search.
- `SearchDocument`: JSON document served from `/search.json`.

## Slugs And URLs

- Blog file `src/content/blog/my-post.md` becomes `/blog/my-post/`.
- Page file `src/content/pages/about.md` becomes `/pages/about/`.
- Tags are normalized with `slugifyTag` in `src/utils/content.ts`.

## Validation Rules

- Do not publish a post without tags.
- Keep descriptions within the schema range so meta descriptions remain useful.
- Set `draft: true` for unfinished content instead of moving files out of the collection.
- Prefer ISO date literals in frontmatter, for example `2026-06-06`.

## Migration Notes

When importing posts from another platform:

1. Move Markdown into `src/content/blog`.
2. Convert frontmatter to the `blog` schema.
3. Check internal links and image paths.
4. Run `npm run build` to catch schema or route errors.
5. Add redirects separately if old URLs must be preserved.