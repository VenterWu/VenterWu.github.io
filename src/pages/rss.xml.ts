import rss from '@astrojs/rss';
import { getPublishedBlogPosts } from '../utils/content';
import { routes, siteConfig, withBase } from '../utils/config';

export async function GET(context: { site?: URL }) {
  const posts = await getPublishedBlogPosts();

  return rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: (context.site ?? new URL(siteConfig.site.url)).toString(),
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.pubDate,
      link: withBase(routes.blogPost(post.slug)),
      categories: post.data.tags,
      author: post.data.author,
    })),
    customData: `<language>${siteConfig.language}</language>`,
  });
}