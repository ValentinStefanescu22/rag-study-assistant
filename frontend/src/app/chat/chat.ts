import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { Api, ChatResponse, Source, errorMessage } from '../api';
import { Segment, answerSegments, uniquePages } from '../citations';

// One question and what came back for it. No response and no error = still waiting.
interface Turn {
  question: string;
  response?: ChatResponse;
  segments?: Segment[]; // the answer split into text and page flags
  pages?: Source[]; // each cited page once, for the list under the answer
  error?: string;
}

@Component({
  selector: 'app-chat',
  templateUrl: './chat.html',
  styleUrl: './chat.css',
})
export class Chat {
  protected readonly api = inject(Api);
  private readonly injector = inject(Injector);
  private readonly end = viewChild.required<ElementRef<HTMLElement>>('end');

  protected readonly turns = signal<Turn[]>([]);
  // computed() derives a value from other signals and updates itself when they change.
  protected readonly asking = computed(() => this.turns().some((t) => !t.response && !t.error));

  protected async ask(box: HTMLTextAreaElement) {
    const question = box.value.trim();
    if (!question || this.asking()) return;
    box.value = '';

    const pending: Turn = { question };
    this.turns.update((turns) => [...turns, pending]);
    this.scrollToEnd();

    try {
      const response = await this.api.ask(question);
      this.replace(pending, {
        question,
        response,
        segments: answerSegments(response.answer, response.sources),
        pages: uniquePages(response.sources),
      });
    } catch (e) {
      this.replace(pending, { question, error: errorMessage(e) });
    }
    this.scrollToEnd();
  }

  // Enter sends, Shift+Enter adds a new line.
  protected onKeydown(event: KeyboardEvent, box: HTMLTextAreaElement) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.ask(box);
    }
  }

  // Swap the pending turn for the finished one (a new array, so the signal notices).
  private replace(old: Turn, next: Turn) {
    this.turns.update((turns) => turns.map((t) => (t === old ? next : t)));
  }

  // Wait until Angular has drawn the new turn, then bring it into view.
  private scrollToEnd() {
    afterNextRender(() => this.end().nativeElement.scrollIntoView({ block: 'end' }), {
      injector: this.injector,
    });
  }
}
