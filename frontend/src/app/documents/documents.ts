import { Component, inject, signal } from '@angular/core';
import { Api, DocumentInfo, errorMessage } from '../api';

@Component({
  selector: 'app-documents',
  templateUrl: './documents.html',
  styleUrl: './documents.css',
})
export class Documents {
  protected readonly api = inject(Api);

  // Signals hold the component's state. Reading one in the template (`documents()`)
  // tells Angular to re-render that part whenever it changes.
  protected readonly documents = signal<DocumentInfo[]>([]);
  protected readonly uploading = signal<string | null>(null); // name of the file being processed
  protected readonly error = signal<string | null>(null);

  constructor() {
    this.refresh();
  }

  private async refresh() {
    try {
      this.documents.set(await this.api.listDocuments());
    } catch (e) {
      this.error.set(errorMessage(e));
    }
  }

  protected async upload(input: HTMLInputElement) {
    const files = Array.from(input.files ?? []);
    input.value = ''; // so picking the same file again still fires (change)
    this.error.set(null);

    // One at a time: each upload embeds every chunk with Ollama, which is the slow part.
    for (const file of files) {
      this.uploading.set(file.name);
      try {
        await this.api.upload(file);
      } catch (e) {
        this.error.set(`${file.name}: ${errorMessage(e)}`);
      }
    }
    this.uploading.set(null);
    await this.refresh();
  }

  protected async remove(doc: DocumentInfo) {
    if (!confirm(`Remove ${doc.filename}? Its answers won't be available until you upload it again.`)) {
      return;
    }
    try {
      await this.api.deleteDocument(doc.id);
      // update() derives the new value from the old one; we build a new array instead of
      // mutating, so the signal sees a change.
      this.documents.update((docs) => docs.filter((d) => d.id !== doc.id));
    } catch (e) {
      this.error.set(errorMessage(e));
    }
  }
}
