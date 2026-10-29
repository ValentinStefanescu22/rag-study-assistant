import { Injectable, computed, inject, signal } from '@angular/core';
import { Api, ChatResponse, DocumentInfo, errorMessage } from './api';
import { FileSources, Segment, answerSegments, sourcesByFile } from './citations';

// One question (or summary request) and what came back for it.
// No response and no error = still waiting.
export interface Turn {
  title: string; // the question, or "Summary of 01-Introduction.pdf"
  waiting: string; // shown while waiting
  hint?: string; // extra line while waiting, e.g. "this takes a few minutes"
  response?: ChatResponse;
  segments?: Segment[]; // the answer split into text and page flags
  files?: FileSources[]; // cited pages grouped by file, for the list under the answer
  error?: string;
}

// The conversation lives in a service, not in the Chat component, because both the chat
// box and the lecture sidebar (Summarize buttons) add to it. `providedIn: 'root'` means one
// shared instance: every component that injects it sees the same signals.
@Injectable({ providedIn: 'root' })
export class Conversation {
  private readonly api = inject(Api);

  readonly turns = signal<Turn[]>([]);
  readonly busy = computed(() => this.turns().some((t) => !t.response && !t.error));

  ask(question: string) {
    return this.run({ title: question, waiting: 'Reading your slides' }, () => this.api.ask(question));
  }

  summarize(doc: DocumentInfo) {
    return this.run(
      {
        title: `Summary of ${doc.filename}`,
        waiting: `Reading all ${doc.page_count} slides`,
        hint: 'The first summary of a lecture takes a few minutes. After that it opens instantly.',
      },
      () => this.api.summarize(doc.id),
    );
  }

  // Add the pending turn, wait for the request, then swap in the finished turn
  // (a new array each time, so the signal notices the change).
  private async run(pending: Turn, request: () => Promise<ChatResponse>) {
    this.turns.update((turns) => [...turns, pending]);
    let done: Turn;
    try {
      const response = await request();
      done = {
        ...pending,
        response,
        segments: answerSegments(response.answer, response.sources),
        files: sourcesByFile(response.sources),
      };
    } catch (e) {
      done = { ...pending, error: errorMessage(e) };
    }
    this.turns.update((turns) => turns.map((t) => (t === pending ? done : t)));
  }
}
