import { getCollection, type CollectionEntry } from 'astro:content';
import { routes, withBase } from './config';

export type PublishedBlogPost = CollectionEntry<'blog'>;
export type PublishedPage = CollectionEntry<'pages'>;

export type TagStat = {
  label: string;
  slug: string;
  count: number;
};

export type SearchDocument = {
  type: 'blog' | 'page';
  title: string;
  description: string;
  href: string;
  tags: string[];
  date?: string;
  content: string;
};

export async function getPublishedBlogPosts(): Promise<PublishedBlogPost[]> {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  return posts.sort((leftPost, rightPost) => rightPost.data.pubDate.valueOf() - leftPost.data.pubDate.valueOf());
}

export async function getPublishedPages(): Promise<PublishedPage[]> {
  const pages = await getCollection('pages', ({ data }) => !data.draft);
  return pages.sort((leftPage, rightPage) => leftPage.data.order - rightPage.data.order);
}

export function slugifyTag(tag: string): string {
  return tag
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function getTagStats(posts: PublishedBlogPost[]): TagStat[] {
  const tagMap = new Map<string, TagStat>();

  for (const post of posts) {
    for (const tag of post.data.tags) {
      const slug = slugifyTag(tag);
      const current = tagMap.get(slug);

      if (current) {
        current.count += 1;
      } else {
        tagMap.set(slug, { label: tag, slug, count: 1 });
      }
    }
  }

  return [...tagMap.values()].sort((leftTag, rightTag) => {
    if (rightTag.count !== leftTag.count) {
      return rightTag.count - leftTag.count;
    }

    return leftTag.label.localeCompare(rightTag.label);
  });
}

export function getPostsByTag(posts: PublishedBlogPost[], tagSlug: string): PublishedBlogPost[] {
  return posts.filter((post) => post.data.tags.some((tag) => slugifyTag(tag) === tagSlug));
}

export function createExcerpt(content: string, maxLength = 220): string {
  const text = stripMarkdown(content);

  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength).trim()}...`;
}

export async function getSearchDocuments(): Promise<SearchDocument[]> {
  const [posts, pages] = await Promise.all([getPublishedBlogPosts(), getPublishedPages()]);

  return [
    ...posts.map((post) => ({
      type: 'blog' as const,
      title: post.data.title,
      description: post.data.description,
      href: withBase(routes.blogPost(post.slug)),
      tags: post.data.tags,
      date: post.data.pubDate.toISOString(),
      content: createExcerpt(post.body, 600),
    })),
    ...pages.map((page) => ({
      type: 'page' as const,
      title: page.data.title,
      description: page.data.description,
      href: withBase(routes.page(page.slug)),
      tags: [],
      content: createExcerpt(page.body, 600),
    })),
  ];
}

export function stripMarkdown(content: string): string {
  return content
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[>#*_~|-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}