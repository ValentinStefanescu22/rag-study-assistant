import { Source } from './api';
import { answerSegments, sourcesByFile, splitCitations } from './citations';

const source = (n: number, page: number, document_id = 1): Source => ({
  n,
  document_id,
  filename: 'intro.pdf',
  page_number: page,
});

describe('splitCitations', () => {
  it('leaves text without citations alone', () => {
    expect(splitCitations('No citations here.')).toEqual([{ kind: 'text', text: 'No citations here.' }]);
  });

  it('splits text around citations', () => {
    expect(splitCitations('Themis [1].')).toEqual([
      { kind: 'text', text: 'Themis ' },
      { kind: 'cite', n: 1 },
      { kind: 'text', text: '.' },
    ]);
  });

  it('handles citations next to each other, with no empty text between them', () => {
    expect(splitCitations('Both [2][3]')).toEqual([
      { kind: 'text', text: 'Both ' },
      { kind: 'cite', n: 2 },
      { kind: 'cite', n: 3 },
    ]);
  });

  it('only treats [number] as a citation', () => {
    expect(splitCitations('An array a[i] and [note]')).toEqual([
      { kind: 'text', text: 'An array a[i] and [note]' },
    ]);
  });
});

describe('answerSegments', () => {
  it('resolves citations to their source', () => {
    expect(answerSegments('Themis [2].', [source(2, 7)])).toEqual([
      { kind: 'text', text: 'Themis ' },
      { kind: 'cite', source: source(2, 7) },
      { kind: 'text', text: '.' },
    ]);
  });

  it('drops citation numbers the backend did not return', () => {
    expect(answerSegments('Made up [9]', [source(1, 4)])).toEqual([{ kind: 'text', text: 'Made up ' }]);
  });

  it('shows the same page once when cited several times in a row', () => {
    const sources = [source(1, 3), source(2, 3), source(3, 5)];
    expect(answerSegments('3NF [1][2][3]', sources)).toEqual([
      { kind: 'text', text: '3NF ' },
      { kind: 'cite', source: source(1, 3) },
      { kind: 'cite', source: source(3, 5) },
    ]);
  });
});

describe('sourcesByFile', () => {
  it('lists each file once, with each page once, in page order', () => {
    const sources = [source(1, 7), source(2, 3), source(3, 7), source(4, 3, 2)];
    expect(sourcesByFile(sources)).toEqual([
      { document_id: 1, filename: 'intro.pdf', pages: [source(2, 3), source(1, 7)] },
      { document_id: 2, filename: 'intro.pdf', pages: [source(4, 3, 2)] },
    ]);
  });
});
