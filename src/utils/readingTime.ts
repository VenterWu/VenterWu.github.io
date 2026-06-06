const WORDS_PER_MINUTE = 220;
const CJK_CHARS_PER_WORD = 2;

export function getReadingTime(content: string): string {
  const words = content.trim().split(/\s+/).filter(Boolean).length;
  const cjkCharacters = content.match(/[\u3400-\u9fff]/g)?.length ?? 0;
  const normalizedWords = Math.max(words, Math.ceil(cjkCharacters / CJK_CHARS_PER_WORD));
  const minutes = Math.max(1, Math.ceil(normalizedWords / WORDS_PER_MINUTE));

  return `${minutes} min read`;
}