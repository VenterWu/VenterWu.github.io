export const siteConfig = {
  site: {
    url: 'https://VenterWu.github.io',
    base: '/',
  },
  title: 'Venter Field Notes',
  description: 'Minimal field notes on software, learning systems, and useful experiments.',
  language: 'en',
  locale: 'en_US',
  author: {
    name: 'Kefan Wu',
    handle: '@kefanwu',
    email: 'hello@example.com',
  },
  nav: [
    { label: 'Home', href: '/' },
    { label: 'Blog', href: '/blog/' },
    { label: 'Tags', href: '/tags/' },
    { label: 'About', href: '/pages/about/' },
  ],
  social: [
    { label: 'GitHub', href: 'https://github.com/VenterWu' },
    { label: 'RSS', href: '/rss.xml' },
  ],
  seo: {
    twitterCard: 'summary_large_image',
    defaultOgSlug: 'site',
  },
} as const;

export const routes = {
  home: '/',
  blog: '/blog/',
  tags: '/tags/',
  rss: '/rss.xml',
  search: '/search.json',
  blogPost: (slug: string) => `/blog/${slug}/`,
  page: (slug: string) => `/pages/${slug}/`,
  tag: (slug: string) => `/tags/${slug}/`,
  og: (slug: string) => `/og/${slug}.svg`,
} as const;

export type SiteConfig = typeof siteConfig;

export function normalizeBase(base: string = siteConfig.site.base): string {
  if (!base || base === '/') {
    return '/';
  }

  const trimmedBase = base.replace(/^\/+|\/+$/g, '');
  return `/${trimmedBase}/`;
}

export function withBase(path: string): string {
  const base = normalizeBase();
  const cleanPath = path.replace(/^\/+/, '');

  if (!cleanPath) {
    return base;
  }

  return base === '/' ? `/${cleanPath}` : `${base}${cleanPath}`;
}

export function getCanonicalUrl(path: string = routes.home): string {
  return new URL(withBase(path), siteConfig.site.url).toString();
}

export function getAssetUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path;
  }

  return getCanonicalUrl(path);
}

export function getOgImageUrl(slug = siteConfig.seo.defaultOgSlug): string {
  return getCanonicalUrl(routes.og(slug));
}