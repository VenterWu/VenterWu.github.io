const DATE_FORMATTER = new Intl.DateTimeFormat('en', {
  year: 'numeric',
  month: 'short',
  day: '2-digit',
});

export function formatDate(date: Date): string {
  return DATE_FORMATTER.format(date);
}

export function toIsoDate(date: Date): string {
  return date.toISOString().split('T')[0];
}