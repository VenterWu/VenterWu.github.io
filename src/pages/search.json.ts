import { getSearchDocuments } from '../utils/content';

export async function GET() {
  const documents = await getSearchDocuments();

  return new Response(
    JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        documents,
      },
      null,
      2,
    ),
    {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'public, max-age=300',
      },
    },
  );
}