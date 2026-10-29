import { Component, ElementRef, Injector, afterNextRender, effect, inject, viewChild } from '@angular/core';
import { Api } from '../api';
import { Conversation } from '../conversation';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.html',
  styleUrl: './chat.css',
})
export class Chat {
  protected readonly api = inject(Api);
  protected readonly conversation = inject(Conversation);
  private readonly injector = inject(Injector);
  private readonly end = viewChild.required<ElementRef<HTMLElement>>('end');

  constructor() {
    // effect() re-runs whenever a signal it reads changes. Here: every time a turn is added
    // or finishes (from this box or from a Summarize button), scroll the newest into view
    // once Angular has drawn it.
    effect(() => {
      this.conversation.turns();
      afterNextRender(() => this.end().nativeElement.scrollIntoView({ block: 'end' }), {
        injector: this.injector,
      });
    });
  }

  protected ask(box: HTMLTextAreaElement) {
    const question = box.value.trim();
    if (!question || this.conversation.busy()) return;
    box.value = '';
    this.conversation.ask(question);
  }

  // Enter sends, Shift+Enter adds a new line.
  protected onKeydown(event: KeyboardEvent, box: HTMLTextAreaElement) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.ask(box);
    }
  }
}
