import { Source } from './api';

export type Part = { kind: 'text'; text: string } | { kind: 'cite'; n: number };
export type Segment = { kind: 'text'; text: string } | { kind: 'cite'; source: Source };

// Splits "Assignments go to Themis [1][2]." into text and citation pieces, so the template
// can render citations as links without ever treating the model's answer as HTML.
// `split` with a capture group keeps the captured numbers: odd positions are citations.
export function splitCitations(answer: string): Part[] {
  return answer
    .split(/\[(\d+)\]/)
    .map((part, i): Part => (i % 2 === 1 ? { kind: 'cite', n: Number(part) } : { kind: 'text', text: part }))
    .filter((part) => part.kind === 'cite' || part.text !== '');
}

// Resolves each [n] to its source (file + page). Drops numbers the backend didn't return,
// and repeats of the same page right next to each other ("p.3 p.3" -> "p.3"), which happen
// because several chunks can come from one page.
export function answerSegments(answer: string, sources: Source[]): Segment[] {
  const segments: Segment[] = [];
  for (const part of splitCitations(answer)) {
    if (part.kind === 'text') {
      segments.push(part);
      continue;
    }
    const source = sources.find((s) => s.n === part.n);
    const previous = segments.at(-1);
    if (!source || (previous?.kind === 'cite' && samePage(previous.source, source))) continue;
    segments.push({ kind: 'cite', source });
  }
  return segments;
}

export interface FileSources {
  document_id: number;
  filename: string;
  pages: Source[];
}

// The source list under an answer: each file once, with each of its cited pages once, in
// page order. A summary can cite 28 pages of one lecture; this shows the filename one time.
export function sourcesByFile(sources: Source[]): FileSources[] {
  const files: FileSources[] = [];
  for (const source of sources) {
    let file = files.find((f) => f.document_id === source.document_id);
    if (!file) {
      file = { document_id: source.document_id, filename: source.filename, pages: [] };
      files.push(file);
    }
    if (!file.pages.some((p) => p.page_number === source.page_number)) file.pages.push(source);
  }
  for (const file of files) file.pages.sort((a, b) => a.page_number - b.page_number);
  return files;
}

function samePage(a: Source, b: Source): boolean {
  return a.document_id === b.document_id && a.page_number === b.page_number;
}
