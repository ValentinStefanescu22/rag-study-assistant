import { Component } from '@angular/core';
import { Chat } from './chat/chat';
import { Documents } from './documents/documents';

// Standalone component: it lists what it uses in `imports`, no NgModule needed.
@Component({
  selector: 'app-root',
  imports: [Documents, Chat],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {}
