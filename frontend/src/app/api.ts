import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

// These mirror the JSON the FastAPI backend returns.
export interface DocumentInfo {
  id: number;
  filename: string;
  page_count: number;
  chunk_count: number;
  uploaded_at: string;
}

export interface Source {
  n: number;
  document_id: number;
  filename: string;
  page_number: number;
}

export interface ChatResponse {
  answer: string;
  found: boolean;
  sources: Source[];
}

// The dev server (proxy.conf.json) and later nginx forward /api/* to the backend,
// so the browser only ever talks to one origin and we need no CORS setup.
const API = '/api';

@Injectable({ providedIn: 'root' })
export class Api {
  private readonly http = inject(HttpClient);

  // HttpClient returns Observables; firstValueFrom turns a one-shot request into a Promise,
  // which reads more simply with async/await.
  listDocuments() {
    return firstValueFrom(this.http.get<DocumentInfo[]>(`${API}/documents`));
  }

  upload(file: File) {
    const form = new FormData(); // multipart/form-data, what FastAPI's UploadFile expects
    form.append('file', file);
    return firstValueFrom(this.http.post(`${API}/documents`, form));
  }

  deleteDocument(id: number) {
    return firstValueFrom(this.http.delete<void>(`${API}/documents/${id}`));
  }

  ask(question: string) {
    return firstValueFrom(this.http.post<ChatResponse>(`${API}/chat`, { question }));
  }

  // The browser's PDF viewer understands #page=N and opens the file on that page.
  fileUrl(documentId: number, page = 1) {
    return `${API}/documents/${documentId}/file#page=${page}`;
  }
}

// Turns any failed request into a sentence the UI can show.
// FastAPI puts its error message in {"detail": "..."}.
export function errorMessage(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) return "Can't reach the server. Check that the backend is running.";
    if (typeof error.error?.detail === 'string') return error.error.detail;
  }
  return 'Something went wrong. Try again.';
}
