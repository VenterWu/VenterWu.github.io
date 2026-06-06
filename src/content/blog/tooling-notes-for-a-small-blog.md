---
title: Tooling Notes For A Small Blog
description: Notes on choosing boring tools for a personal blog that should be easy to build and deploy.
pubDate: 2026-05-21
author: Kefan Wu
tags: [typescript, deployment, astro]
---

## Prefer Static Output

Static output makes deployment predictable. GitHub Pages can host the compiled site directly, and every route is generated during the build. That means broken content schema, missing imports, or route mistakes are caught before publishing.

## Centralize Replaceable Values

The public URL and base path are the easiest values to forget during a migration. This project keeps them in `src/utils/config.ts` so the same source feeds Astro config, canonical URLs, navigation links, RSS links, and search results.

## Use Content Collections

Astro Content Collections make Markdown feel like typed data. Lists, tag pages, RSS, search, and SEO helpers can all rely on the same validated frontmatter instead of parsing loose objects in each route.

## Keep Interaction Local

Theme switching and search are useful, but they do not need a framework island. A small script attached to the relevant component keeps the static-first model intact while still giving readers a smoother experience.