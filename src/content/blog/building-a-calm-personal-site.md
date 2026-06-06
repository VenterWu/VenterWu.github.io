---
title: Building A Calm Personal Site
description: A practical note on shaping a personal site around writing, search, and a small static stack.
pubDate: 2026-06-06
author: Kefan Wu
tags: [astro, writing, web]
featured: true
---

## Start With The Reader

A personal site does not need to open with a sales pitch. It should help a reader understand what is here, what changed recently, and where to go next.

This MVP starts with the writing surface: recent posts, tags, search, RSS, and stable pages. The design keeps the first screen useful instead of treating the blog like a product landing page.

## Keep The Stack Small

Astro is a good fit because most of the site can be generated as static HTML. Markdown content stays portable, TypeScript keeps route helpers honest, and Tailwind gives the project a practical styling vocabulary without introducing a component runtime.

The only client-side code in the MVP handles theme switching and search. Both are plain JavaScript and can be removed or replaced without changing the content model.

## Leave Room For Growth

The project can grow through collections. A future `projects` collection could reuse the same layout and SEO helpers, while a migration script can use the `psblog` Python environment to normalize imported Markdown.

The important part is that the first version already has clear boundaries: content schema, site config, layouts, components, and generated feeds.