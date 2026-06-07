import type { APIRoute } from 'astro';
import { getPublishedBlogPosts, getPublishedPages } from '../../utils/content';
import { siteConfig } from '../../utils/config';

type OgProps = {
  title: string;
  description: string;
  label: string;
};

export async function getStaticPaths() {
  const [posts, pages] = await Promise.all([getPublishedBlogPosts(), getPublishedPages()]);

  return [
    {
      params: { slug: siteConfig.seo.defaultOgSlug },
      props: {
        title: siteConfig.title,
        description: siteConfig.description,
        label: 'Personal Blog',
      },
    },
    ...posts.map((post) => ({
      params: { slug: post.slug },
      props: {
        title: post.data.title,
        description: post.data.description,
        label: 'Blog Post',
      },
    })),
    ...pages.map((page) => ({
      params: { slug: `page-${page.slug}` },
      props: {
        title: page.data.title,
        description: page.data.description,
        label: 'Page',
      },
    })),
  ];
}

export const GET: APIRoute = ({ props }) => {
  const ogProps = props as OgProps;

  return new Response(renderOgSvg(ogProps), {
    headers: {
      'Content-Type': 'image/svg+xml; charset=utf-8',
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
};

function renderOgSvg(props: OgProps): string {
  const title = escapeXml(props.title);
  const description = escapeXml(props.description);
  const label = escapeXml(props.label);

  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#fffdf8" />
      <stop offset="56%" stop-color="#f8f5ee" />
      <stop offset="100%" stop-color="#ede7dc" />
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)" />
  <rect x="72" y="72" width="1056" height="486" rx="18" fill="#fffdf8" stroke="#ccc3b5" stroke-width="2" />
  <circle cx="1098" cy="108" r="10" fill="#977634" />
  <text x="112" y="139" fill="#977634" font-family="Georgia, serif" font-size="22" font-weight="700">${label}</text>
  <text x="112" y="258" fill="#332c25" font-family="Georgia, serif" font-size="64" font-weight="700">
    ${wrapSvgText(title, 28, 112, 0, 76)}
  </text>
  <text x="112" y="458" fill="#6f655a" font-family="Arial, sans-serif" font-size="30" font-weight="500">
    ${wrapSvgText(description, 54, 112, 0, 42)}
  </text>
  <text x="112" y="522" fill="#977634" font-family="Arial, sans-serif" font-size="24" font-weight="700">${escapeXml(siteConfig.site.url.replace(/^https?:\/\//, ''))}</text>
</svg>`;
}

function wrapSvgText(text: string, lineLength: number, x: number, yOffset: number, lineHeight: number): string {
  const words = text.split(' ');
  const lines: string[] = [];
  let currentLine = '';

  for (const word of words) {
    const nextLine = currentLine ? `${currentLine} ${word}` : word;
    if (nextLine.length > lineLength && currentLine) {
      lines.push(currentLine);
      currentLine = word;
    } else {
      currentLine = nextLine;
    }
  }

  if (currentLine) {
    lines.push(currentLine);
  }

  return lines
    .slice(0, 2)
    .map((line, index) => `<tspan x="${x}" dy="${index === 0 ? yOffset : lineHeight}">${escapeXml(line)}</tspan>`)
    .join('');
}

function escapeXml(value: string): string {
  return value.replace(/[<>&"']/g, (character) => {
    const entities: Record<string, string> = {
      '<': '&lt;',
      '>': '&gt;',
      '&': '&amp;',
      '"': '&quot;',
      "'": '&apos;',
    };

    return entities[character];
  });
}