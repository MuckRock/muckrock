# FOIA Coach SvelteKit UI - Implementation Plan

## How to Use This Plan

This plan is designed for **incremental implementation across multiple Claude Code sessions**:

1. **Start each session** by referencing this document: `@.claude/plans/foia-coach-ui.md`
2. **Focus on one phase per session** to keep context clean and manageable
3. **Update progress** in the Progress Tracker table after completing each phase
4. **Mark tasks complete** with ✅ and add completion notes
5. **Docker-first approach**: All development happens in containers to avoid Node version conflicts

## Progress Tracker

**Last Updated:** 2025-12-10

| Phase | Status | Completed | Notes |
|-------|--------|-----------|-------|
| Phase 1: SvelteKit Project Scaffold | ✅ Complete | 2025-12-10 | Docker setup with Node 20, basic routes, navigation |
| Phase 2: API Client & Settings | ✅ Complete | 2025-12-10 | Settings store, API client, Settings component with test connection |
| Phase 3: Chat UI Components | ✅ Complete | 2025-12-10 | Chat store, ChatMessage and ChatHistory components with test messages |
| Phase 4: Query Form & Integration | ✅ Complete | 2025-12-10 | QueryForm with jurisdiction selector, API integration, error handling |
| Phase 5: Context Management | ✅ Complete | 2025-12-10 | Context store with localStorage, conversation history tracking |
| Phase 6: Polish & Testing | ✅ Complete | 2025-12-10 | Enhanced UI styling, responsive design, complete testing |

---

## Executive Summary

Create a simple SvelteKit frontend using Svelte 5 to provide an interactive chat interface for the FOIA Coach API. The UI will allow users to ask questions about state public records laws and receive AI-powered coaching from the Gemini-powered backend.

## Problem Statement

**Need:**
- Interactive chat interface to query the FOIA Coach API
- Maintain conversation context for follow-up questions
- Configure API connection settings
- Simple, clean UX for experimentation

**Solution:**
Minimal SvelteKit application with chat UI, context management, and configurable settings.

---

## Architecture Overview

### Application Topology

```
┌─────────────────────────────────┐
│   FOIA Coach API Service        │
│   Port: 8001                    │
│   - Django REST API             │
│   - Gemini File Search          │
│   - Jurisdiction resources      │
└─────────────┬───────────────────┘
              │
              │ HTTP/REST
              │ CORS enabled
              │
┌─────────────▼───────────────────┐
│   SvelteKit Frontend            │
│   Port: 5173                    │
│   - Svelte 5 (Runes API)        │
│   - Chat UI                     │
│   - API Client                  │
│   - LocalStorage settings       │
└─────────────────────────────────┘
```

**Authentication Note:**
- UI → FOIA Coach API: No authentication required for local development
- FOIA Coach API → Gemini: Handled internally by the microservice
- API token field in UI is optional, only needed for remote/production deployments

**Initial Scope:**
- Starting with 3 states: Colorado (CO), Georgia (GA), Tennessee (TN)
- Can expand to additional states in future phases

### Tech Stack

- **Framework:** SvelteKit (latest) with Svelte 5
- **Language:** TypeScript (optional, can use JavaScript)
- **State Management:** Svelte stores + runes
- **HTTP Client:** Native fetch API
- **Persistence:** localStorage for settings
- **Styling:** Minimal CSS (no framework needed)

---

## Project Structure

```
foia-coach-ui/
├── package.json
├── svelte.config.js
├── vite.config.js
├── src/
│   ├── app.html                    # App shell
│   ├── routes/
│   │   ├── +page.svelte           # Main chat interface
│   │   └── settings/
│   │       └── +page.svelte       # Settings page
│   ├── lib/
│   │   ├── api/
│   │   │   └── client.ts          # API client for FOIA Coach API
│   │   ├── stores/
│   │   │   ├── settings.svelte.ts # Settings store (with runes)
│   │   │   └── chat.svelte.ts     # Chat history store (with runes)
│   │   └── components/
│   │       ├── ChatMessage.svelte # Individual message display
│   │       ├── ChatHistory.svelte # Message list
│   │       ├── QueryForm.svelte   # Query input form
│   │       └── Settings.svelte    # Settings form
│   └── app.css                     # Global styles
└── static/
    └── favicon.png
```

---

## Implementation Phases

Each phase is designed to:
- **Complete in 30 minutes to 1 hour**
- Fit within single Claude Code session
- Result in a working, committable state
- Be independently testable
- Build incrementally on previous phases

**Note:** Focus on functionality first, polish later. This is an experimental UI.

---

### Phase 1: SvelteKit Project Scaffold (30-45 minutes) ✅ COMPLETE

**Goal:** Initialize SvelteKit project with basic structure and routing in Docker container.

**Note:** Using Docker with Node 20 to avoid conflicts with main MuckRock project (Node 18).

#### Docker Setup (COMPLETED)

**Files Created:**
- `foia-coach-ui/compose/local/Dockerfile` - Node 20 Alpine container
- Updated `local.yml` with `foia_coach_ui` service

**Docker Configuration:**
```yaml
foia_coach_ui:
  build:
    context: ./foia-coach-ui
    dockerfile: ./compose/local/Dockerfile
  image: muckrock_foia_coach_ui_local
  container_name: foia_coach_ui_local
  volumes:
    - ./foia-coach-ui:/app:z
    - /app/node_modules
  ports:
    - "5173:5173"
  command: npm run dev -- --host 0.0.0.0
```

**Important:** Updated `package.json` to use `@types/node@^20.19.0` for Vite 7 compatibility.

#### Tasks (COMPLETED)

1. **Create SvelteKit project** ✅
   - Used `npx sv create foia-coach-ui`
   - Selected: Skeleton project, TypeScript, ESLint, Prettier

2. **Install dependencies in Docker** ✅
   - Fixed `@types/node` version conflict (18 → 20)
   - Built container: `docker compose -f local.yml build foia_coach_ui`

3. **Create basic route structure** ✅
   - Main page: `src/routes/+page.svelte` (chat interface)
   - Settings page: `src/routes/settings/+page.svelte`

4. **Create basic layout** ✅ (src/routes/+layout.svelte)
   ```svelte
   - Layout includes navigation and global styles
   - Uses Svelte 5 syntax with `{@render children()}`

5. **Create placeholder pages** ✅
   - Main page: "FOIA Coach" heading with placeholder text
   - Settings page: "Settings" heading with placeholder text

6. **Add basic global styles** ✅ (src/app.css)
   - Reset styles, typography, link colors

7. **Test development server** ✅
   ```bash
   docker compose -f local.yml up foia_coach_ui -d
   docker compose -f local.yml logs foia_coach_ui
   # Visit http://localhost:5173
   ```

#### Deliverables

- ✅ SvelteKit project initialized
- ✅ Dependencies installed in Docker container
- ✅ Basic routing configured (/ and /settings)
- ✅ Layout with navigation
- ✅ Dev server running in Docker
- ✅ Can navigate between pages

#### Success Criteria

```bash
# Start container
docker compose -f local.yml up foia_coach_ui -d

# Check logs
docker compose -f local.yml logs foia_coach_ui

# Browser test:
# 1. Visit http://localhost:5173 - Shows "FOIA Coach" heading ✅
# 2. Click "Settings" link - Navigates to settings page ✅
# 3. Click "Chat" link - Returns to main page ✅
```

#### Key Docker Commands

```bash
# Build container
docker compose -f local.yml build foia_coach_ui

# Start container
docker compose -f local.yml up foia_coach_ui -d

# Stop container
docker compose -f local.yml stop foia_coach_ui

# View logs
docker compose -f local.yml logs foia_coach_ui --tail=50

# Restart container (after code changes that need rebuild)
docker compose -f local.yml restart foia_coach_ui
```

---

### Phase 2: API Client & Settings Management (45-60 minutes)

**Goal:** Create API client and settings management with localStorage persistence.

**Note:** Settings needed before chat can work. This phase creates the foundation.

#### Tasks

1. **Create settings store** (src/lib/stores/settings.svelte.ts)
   ```typescript
   import { browser } from '$app/environment';

   // Settings interface
   export interface Settings {
     apiUrl: string;
     apiToken: string;
     geminiModel: string;
   }

   // Default settings
   const defaultSettings: Settings = {
     apiUrl: 'http://localhost:8001',
     apiToken: '',
     geminiModel: 'gemini-2.0-flash-001'
   };

   // Load from localStorage or use defaults
   function loadSettings(): Settings {
     if (!browser) return defaultSettings;

     const stored = localStorage.getItem('foia-coach-settings');
     if (stored) {
       try {
         return { ...defaultSettings, ...JSON.parse(stored) };
       } catch (e) {
         console.error('Failed to parse settings:', e);
       }
     }
     return defaultSettings;
   }

   // Create reactive state using Svelte 5 runes
   class SettingsStore {
     settings = $state(loadSettings());

     update(newSettings: Partial<Settings>) {
       this.settings = { ...this.settings, ...newSettings };
       this.save();
     }

     save() {
       if (browser) {
         localStorage.setItem('foia-coach-settings', JSON.stringify(this.settings));
       }
     }

     reset() {
       this.settings = defaultSettings;
       if (browser) {
         localStorage.removeItem('foia-coach-settings');
       }
     }
   }

   export const settingsStore = new SettingsStore();
   ```

2. **Create API client** (src/lib/api/client.ts)
   ```typescript
   import { settingsStore } from '$lib/stores/settings.svelte';

   export interface QueryRequest {
     question: string;
     state?: string;
     context?: any;
   }

   export interface QueryResponse {
     answer: string;
     citations: Array<{
       source: string;
       content: string;
     }>;
     state?: string;
   }

   export interface Jurisdiction {
     id: number;
     name: string;
     abbrev: string;
     level: string;
   }

   class APIClient {
     private getBaseUrl(): string {
       return settingsStore.settings.apiUrl;
     }

     private getHeaders(): HeadersInit {
       const headers: HeadersInit = {
         'Content-Type': 'application/json',
       };

       const token = settingsStore.settings.apiToken;
       if (token) {
         headers['Authorization'] = `Token ${token}`;
       }

       return headers;
     }

     async query(request: QueryRequest): Promise<QueryResponse> {
       const response = await fetch(`${this.getBaseUrl()}/api/v1/query/query/`, {
         method: 'POST',
         headers: this.getHeaders(),
         body: JSON.stringify(request),
       });

       if (!response.ok) {
         throw new Error(`API error: ${response.status} ${response.statusText}`);
       }

       return response.json();
     }

     async getJurisdictions(): Promise<Jurisdiction[]> {
       const response = await fetch(`${this.getBaseUrl()}/api/v1/jurisdictions/`, {
         headers: this.getHeaders(),
       });

       if (!response.ok) {
         throw new Error(`API error: ${response.status}`);
       }

       const data = await response.json();
       return data.results || data;
     }

     async testConnection(): Promise<boolean> {
       try {
         await this.getJurisdictions();
         return true;
       } catch (e) {
         console.error('Connection test failed:', e);
         return false;
       }
     }
   }

   export const apiClient = new APIClient();
   ```

3. **Create Settings component** (src/lib/components/Settings.svelte)
   ```svelte
   <script lang="ts">
     import { settingsStore } from '$lib/stores/settings.svelte';
     import { apiClient } from '$lib/api/client';

     let testing = $state(false);
     let testResult = $state<string | null>(null);

     async function testConnection() {
       testing = true;
       testResult = null;

       try {
         const success = await apiClient.testConnection();
         testResult = success ? 'Connection successful!' : 'Connection failed';
       } catch (e) {
         testResult = `Error: ${e.message}`;
       } finally {
         testing = false;
       }
     }

     function handleSubmit(event: Event) {
       event.preventDefault();
       settingsStore.save();
       alert('Settings saved!');
     }

     function handleReset() {
       if (confirm('Reset to default settings?')) {
         settingsStore.reset();
       }
     }
   </script>

   <form onsubmit={handleSubmit}>
     <div class="field">
       <label for="apiUrl">FOIA Coach API URL</label>
       <input
         id="apiUrl"
         type="text"
         bind:value={settingsStore.settings.apiUrl}
         placeholder="http://localhost:8001"
         required
       />
       <small>Base URL for the FOIA Coach API service</small>
     </div>

     <div class="field">
       <label for="apiToken">API Token (optional)</label>
       <input
         id="apiToken"
         type="password"
         bind:value={settingsStore.settings.apiToken}
         placeholder="Leave blank for local development"
       />
       <small>Optional token for remote deployments (not needed for local development)</small>
     </div>

     <div class="field">
       <label for="geminiModel">Gemini Model</label>
       <input
         id="geminiModel"
         type="text"
         bind:value={settingsStore.settings.geminiModel}
         placeholder="gemini-2.0-flash-001"
         required
       />
       <small>Gemini model identifier (backend configuration)</small>
     </div>

     <div class="actions">
       <button type="submit">Save Settings</button>
       <button type="button" onclick={handleReset}>Reset to Defaults</button>
       <button type="button" onclick={testConnection} disabled={testing}>
         {testing ? 'Testing...' : 'Test Connection'}
       </button>
     </div>

     {#if testResult}
       <div class="test-result" class:success={testResult.includes('successful')}>
         {testResult}
       </div>
     {/if}
   </form>

   <style>
     form {
       max-width: 600px;
     }

     .field {
       margin-bottom: 1.5rem;
     }

     label {
       display: block;
       font-weight: 600;
       margin-bottom: 0.5rem;
     }

     input {
       width: 100%;
       padding: 0.5rem;
       border: 1px solid #ccc;
       border-radius: 4px;
       font-size: 1rem;
     }

     small {
       display: block;
       color: #666;
       margin-top: 0.25rem;
     }

     .actions {
       display: flex;
       gap: 0.5rem;
       flex-wrap: wrap;
     }

     button {
       padding: 0.5rem 1rem;
       border: none;
       border-radius: 4px;
       cursor: pointer;
       font-size: 1rem;
     }

     button[type="submit"] {
       background: #0066cc;
       color: white;
     }

     button[type="button"] {
       background: #f0f0f0;
       color: #333;
     }

     button:disabled {
       opacity: 0.5;
       cursor: not-allowed;
     }

     .test-result {
       margin-top: 1rem;
       padding: 0.75rem;
       border-radius: 4px;
       background: #ffebee;
       color: #c62828;
     }

     .test-result.success {
       background: #e8f5e9;
       color: #2e7d32;
     }
   </style>
   ```

4. **Update settings page** (src/routes/settings/+page.svelte)
   ```svelte
   <script>
     import Settings from '$lib/components/Settings.svelte';
   </script>

   <h1>Settings</h1>
   <p>Configure your FOIA Coach API connection</p>

   <Settings />
   ```

5. **Test settings persistence**
   - Save settings in browser
   - Reload page
   - Verify settings persisted
   - Test connection button

#### Deliverables

- [ ] Settings store created with localStorage persistence
- [ ] API client created with typed interfaces
- [ ] Settings component with form validation
- [ ] Test connection functionality
- [ ] Settings save and load correctly

#### Success Criteria

```bash
npm run dev

# Browser test:
# 1. Visit http://localhost:5173/settings
# 2. Enter API URL: http://localhost:8001
# 3. Click "Save Settings"
# 4. Reload page - settings should persist
# 5. Click "Test Connection" - should succeed if API is running
# 6. Check browser localStorage - should contain settings
```

---

### Phase 3: Chat UI Components (45-60 minutes)

**Goal:** Build chat message display components for showing conversation history.

**Note:** Just display components - no API integration yet. Focus on UI structure.

#### Tasks

1. **Create chat store** (src/lib/stores/chat.svelte.ts)
   ```typescript
   export interface ChatMessage {
     id: string;
     role: 'user' | 'assistant';
     content: string;
     timestamp: Date;
     citations?: Array<{
       source: string;
       content: string;
     }>;
     state?: string;
   }

   class ChatStore {
     messages = $state<ChatMessage[]>([]);
     isLoading = $state(false);

     addMessage(message: Omit<ChatMessage, 'id' | 'timestamp'>) {
       this.messages.push({
         ...message,
         id: crypto.randomUUID(),
         timestamp: new Date(),
       });
     }

     clear() {
       this.messages = [];
     }

     setLoading(loading: boolean) {
       this.isLoading = loading;
     }
   }

   export const chatStore = new ChatStore();
   ```

2. **Create ChatMessage component** (src/lib/components/ChatMessage.svelte)
   ```svelte
   <script lang="ts">
     import type { ChatMessage } from '$lib/stores/chat.svelte';

     interface Props {
       message: ChatMessage;
     }

     let { message }: Props = $props();

     function formatTime(date: Date): string {
       return date.toLocaleTimeString('en-US', {
         hour: 'numeric',
         minute: '2-digit',
       });
     }
   </script>

   <div class="message" class:user={message.role === 'user'} class:assistant={message.role === 'assistant'}>
     <div class="message-header">
       <span class="role">{message.role === 'user' ? 'You' : 'FOIA Coach'}</span>
       <span class="timestamp">{formatTime(message.timestamp)}</span>
       {#if message.state}
         <span class="state-badge">{message.state}</span>
       {/if}
     </div>

     <div class="message-content">
       {message.content}
     </div>

     {#if message.citations && message.citations.length > 0}
       <div class="citations">
         <h4>Sources:</h4>
         <ul>
           {#each message.citations as citation}
             <li>
               <strong>{citation.source}</strong>
               <p>{citation.content}</p>
             </li>
           {/each}
         </ul>
       </div>
     {/if}
   </div>

   <style>
     .message {
       margin-bottom: 1.5rem;
       padding: 1rem;
       border-radius: 8px;
       max-width: 80%;
     }

     .message.user {
       background: #e3f2fd;
       margin-left: auto;
     }

     .message.assistant {
       background: #f5f5f5;
       margin-right: auto;
     }

     .message-header {
       display: flex;
       gap: 0.5rem;
       align-items: center;
       margin-bottom: 0.5rem;
       font-size: 0.875rem;
     }

     .role {
       font-weight: 600;
     }

     .timestamp {
       color: #666;
     }

     .state-badge {
       padding: 0.125rem 0.5rem;
       background: #fff3cd;
       border-radius: 4px;
       font-size: 0.75rem;
     }

     .message-content {
       white-space: pre-wrap;
       word-wrap: break-word;
     }

     .citations {
       margin-top: 1rem;
       padding-top: 1rem;
       border-top: 1px solid #ddd;
     }

     .citations h4 {
       margin: 0 0 0.5rem 0;
       font-size: 0.875rem;
       color: #666;
     }

     .citations ul {
       margin: 0;
       padding-left: 1.5rem;
     }

     .citations li {
       margin-bottom: 0.5rem;
     }

     .citations p {
       margin: 0.25rem 0 0 0;
       font-size: 0.875rem;
       color: #666;
     }
   </style>
   ```

3. **Create ChatHistory component** (src/lib/components/ChatHistory.svelte)
   ```svelte
   <script lang="ts">
     import { chatStore } from '$lib/stores/chat.svelte';
     import ChatMessage from './ChatMessage.svelte';
     import { onMount } from 'svelte';

     let chatContainer: HTMLDivElement;

     // Auto-scroll to bottom when new messages arrive
     $effect(() => {
       if (chatStore.messages.length > 0 && chatContainer) {
         chatContainer.scrollTop = chatContainer.scrollHeight;
       }
     });
   </script>

   <div class="chat-history" bind:this={chatContainer}>
     {#if chatStore.messages.length === 0}
       <div class="empty-state">
         <h2>Welcome to FOIA Coach</h2>
         <p>Ask a question about state public records laws to get started.</p>
       </div>
     {:else}
       {#each chatStore.messages as message (message.id)}
         <ChatMessage {message} />
       {/each}
     {/if}

     {#if chatStore.isLoading}
       <div class="loading">
         <span>FOIA Coach is thinking...</span>
       </div>
     {/if}
   </div>

   <style>
     .chat-history {
       height: calc(100vh - 300px);
       min-height: 400px;
       overflow-y: auto;
       padding: 1rem;
       border: 1px solid #ddd;
       border-radius: 8px;
       background: white;
     }

     .empty-state {
       display: flex;
       flex-direction: column;
       align-items: center;
       justify-content: center;
       height: 100%;
       text-align: center;
       color: #666;
     }

     .empty-state h2 {
       margin: 0 0 0.5rem 0;
     }

     .empty-state p {
       margin: 0;
     }

     .loading {
       text-align: center;
       padding: 1rem;
       color: #666;
       font-style: italic;
     }
   </style>
   ```

4. **Update main page to show chat** (src/routes/+page.svelte)
   ```svelte
   <script>
     import ChatHistory from '$lib/components/ChatHistory.svelte';
     import { chatStore } from '$lib/stores/chat.svelte';

     // Add some test messages for visualization
     function addTestMessages() {
       chatStore.addMessage({
         role: 'user',
         content: 'What is the response time for FOIA requests in Colorado?',
         state: 'CO',
       });

       chatStore.addMessage({
         role: 'assistant',
         content: 'In Colorado, under the Colorado Open Records Act (CORA), public entities must respond to records requests within 3 business days. However, this response can be to acknowledge the request and provide a timeline for when the records will be available.',
         citations: [
           {
             source: 'Colorado CORA Guide',
             content: 'Response time: 3 business days to respond or acknowledge',
           },
         ],
         state: 'CO',
       });
     }
   </script>

   <div class="page">
     <div class="header">
       <h1>FOIA Coach</h1>
       <button onclick={addTestMessages}>Add Test Messages</button>
       <button onclick={() => chatStore.clear()}>Clear Chat</button>
     </div>

     <ChatHistory />
   </div>

   <style>
     .page {
       max-width: 900px;
       margin: 0 auto;
     }

     .header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       margin-bottom: 1rem;
     }

     button {
       padding: 0.5rem 1rem;
       border: none;
       border-radius: 4px;
       background: #f0f0f0;
       cursor: pointer;
     }

     button:hover {
       background: #e0e0e0;
     }
   </style>
   ```

#### Deliverables

- [ ] Chat store created with message management
- [ ] ChatMessage component with styling
- [ ] ChatHistory component with auto-scroll
- [ ] Test messages display correctly
- [ ] Empty state shows when no messages
- [ ] Loading state displays

#### Success Criteria

```bash
npm run dev

# Browser test:
# 1. Visit http://localhost:5173
# 2. See "Welcome to FOIA Coach" empty state
# 3. Click "Add Test Messages" button
# 4. See user message (blue background, right-aligned)
# 5. See assistant message (gray background, left-aligned)
# 6. See citations section under assistant message
# 7. Click "Clear Chat" - messages disappear
```

---

### Phase 4: Query Form & API Integration (45-60 minutes)

**Goal:** Create query input form and connect it to the FOIA Coach API.

**Note:** This is where the app becomes functional - real queries to real API.

#### Tasks

1. **Create QueryForm component** (src/lib/components/QueryForm.svelte)
   ```svelte
   <script lang="ts">
     import { chatStore } from '$lib/stores/chat.svelte';
     import { apiClient } from '$lib/api/client';

     let question = $state('');
     let selectedState = $state('');
     let error = $state<string | null>(null);

     // Initial states: CO, TN, GA (can expand later)
     const states = [
       { abbrev: '', name: 'All States (General)' },
       { abbrev: 'CO', name: 'Colorado' },
       { abbrev: 'GA', name: 'Georgia' },
       { abbrev: 'TN', name: 'Tennessee' },
     ];

     async function handleSubmit(event: Event) {
       event.preventDefault();

       if (!question.trim()) {
         return;
       }

       error = null;
       chatStore.setLoading(true);

       // Add user message
       chatStore.addMessage({
         role: 'user',
         content: question,
         state: selectedState || undefined,
       });

       try {
         // Get conversation context (all previous messages)
         const context = chatStore.messages.map(msg => ({
           role: msg.role,
           content: msg.content,
         }));

         // Query API
         const response = await apiClient.query({
           question,
           state: selectedState || undefined,
           context,
         });

         // Add assistant response
         chatStore.addMessage({
           role: 'assistant',
           content: response.answer,
           citations: response.citations,
           state: response.state,
         });

         // Clear form
         question = '';
       } catch (e) {
         error = e.message;
         console.error('Query failed:', e);
       } finally {
         chatStore.setLoading(false);
       }
     }
   </script>

   <form onsubmit={handleSubmit} class="query-form">
     {#if error}
       <div class="error">
         Error: {error}
       </div>
     {/if}

     <div class="form-row">
       <select bind:value={selectedState}>
         {#each states as state}
           <option value={state.abbrev}>{state.name}</option>
         {/each}
       </select>

       <input
         type="text"
         bind:value={question}
         placeholder="Ask a question about public records laws..."
         disabled={chatStore.isLoading}
         required
       />

       <button type="submit" disabled={chatStore.isLoading}>
         {chatStore.isLoading ? 'Sending...' : 'Ask'}
       </button>
     </div>
   </form>

   <style>
     .query-form {
       margin-top: 1rem;
     }

     .error {
       padding: 0.75rem;
       margin-bottom: 0.5rem;
       background: #ffebee;
       color: #c62828;
       border-radius: 4px;
     }

     .form-row {
       display: flex;
       gap: 0.5rem;
     }

     select {
       padding: 0.75rem;
       border: 1px solid #ccc;
       border-radius: 4px;
       font-size: 1rem;
       background: white;
       min-width: 200px;
     }

     input {
       flex: 1;
       padding: 0.75rem;
       border: 1px solid #ccc;
       border-radius: 4px;
       font-size: 1rem;
     }

     button {
       padding: 0.75rem 1.5rem;
       border: none;
       border-radius: 4px;
       background: #0066cc;
       color: white;
       font-size: 1rem;
       cursor: pointer;
       white-space: nowrap;
     }

     button:hover:not(:disabled) {
       background: #0052a3;
     }

     button:disabled {
       background: #ccc;
       cursor: not-allowed;
     }
   </style>
   ```

2. **Update main page with query form** (src/routes/+page.svelte)
   ```svelte
   <script>
     import ChatHistory from '$lib/components/ChatHistory.svelte';
     import QueryForm from '$lib/components/QueryForm.svelte';
     import { chatStore } from '$lib/stores/chat.svelte';
   </script>

   <div class="page">
     <div class="header">
       <h1>FOIA Coach</h1>
       <button onclick={() => chatStore.clear()}>Clear Chat</button>
     </div>

     <ChatHistory />
     <QueryForm />
   </div>

   <style>
     .page {
       max-width: 900px;
       margin: 0 auto;
     }

     .header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       margin-bottom: 1rem;
     }

     button {
       padding: 0.5rem 1rem;
       border: none;
       border-radius: 4px;
       background: #f0f0f0;
       cursor: pointer;
     }

     button:hover {
       background: #e0e0e0;
     }
   </style>
   ```

3. **Test with real API**
   - Ensure FOIA Coach API is running (port 8001)
   - Submit a test query
   - Verify response displays correctly
   - Test error handling (stop API and submit query)

#### Deliverables

- [ ] QueryForm component created
- [ ] State selector working
- [ ] Form submits to API
- [ ] User message added to chat
- [ ] API response displayed
- [ ] Loading state works
- [ ] Error handling works

#### Success Criteria

```bash
# Start API first
docker compose -f local.yml up foia_coach_api

# Start UI
cd foia-coach-ui
npm run dev

# Browser test:
# 1. Visit http://localhost:5173
# 2. Select "Colorado" from state dropdown
# 3. Enter question: "What is the response time for FOIA requests?"
# 4. Click "Ask" button
# 5. See user message added immediately
# 6. See loading indicator
# 7. See assistant response with answer and citations
# 8. Try with API stopped - should show error message
```

---

### Phase 5: Context Management & "Start Over" (30-45 minutes)

**Goal:** Implement conversation context accumulation and reset functionality.

**Note:** Context is already being sent in Phase 4 - this phase adds UI controls and session management.

#### Tasks

1. **Update chat store with session management** (src/lib/stores/chat.svelte.ts)
   ```typescript
   import { browser } from '$app/environment';

   export interface ChatMessage {
     id: string;
     role: 'user' | 'assistant';
     content: string;
     timestamp: Date;
     citations?: Array<{
       source: string;
       content: string;
     }>;
     state?: string;
   }

   export interface ChatSession {
     id: string;
     startedAt: Date;
     messages: ChatMessage[];
   }

   class ChatStore {
     messages = $state<ChatMessage[]>([]);
     isLoading = $state(false);
     sessionId = $state(crypto.randomUUID());
     sessionStartedAt = $state(new Date());

     addMessage(message: Omit<ChatMessage, 'id' | 'timestamp'>) {
       this.messages.push({
         ...message,
         id: crypto.randomUUID(),
         timestamp: new Date(),
       });
       this.saveSession();
     }

     clear() {
       this.messages = [];
       this.saveSession();
     }

     startOver() {
       this.messages = [];
       this.sessionId = crypto.randomUUID();
       this.sessionStartedAt = new Date();
       this.saveSession();
     }

     setLoading(loading: boolean) {
       this.isLoading = loading;
     }

     getContext() {
       return this.messages.map(msg => ({
         role: msg.role,
         content: msg.content,
       }));
     }

     private saveSession() {
       if (browser) {
         const session: ChatSession = {
           id: this.sessionId,
           startedAt: this.sessionStartedAt,
           messages: this.messages,
         };
         localStorage.setItem('foia-coach-session', JSON.stringify(session));
       }
     }

     loadSession() {
       if (browser) {
         const stored = localStorage.getItem('foia-coach-session');
         if (stored) {
           try {
             const session: ChatSession = JSON.parse(stored);
             this.sessionId = session.id;
             this.sessionStartedAt = new Date(session.startedAt);
             this.messages = session.messages.map(msg => ({
               ...msg,
               timestamp: new Date(msg.timestamp),
             }));
           } catch (e) {
             console.error('Failed to load session:', e);
           }
         }
       }
     }
   }

   export const chatStore = new ChatStore();
   ```

2. **Add session info display** (src/lib/components/SessionInfo.svelte)
   ```svelte
   <script lang="ts">
     import { chatStore } from '$lib/stores/chat.svelte';

     function formatDateTime(date: Date): string {
       return date.toLocaleString('en-US', {
         month: 'short',
         day: 'numeric',
         hour: 'numeric',
         minute: '2-digit',
       });
     }

     function handleStartOver() {
       if (chatStore.messages.length === 0) {
         return;
       }

       if (confirm('Start a new conversation? This will clear the current chat history and context.')) {
         chatStore.startOver();
       }
     }
   </script>

   <div class="session-info">
     <div class="info">
       <span class="label">Session started:</span>
       <span class="value">{formatDateTime(chatStore.sessionStartedAt)}</span>
       <span class="separator">•</span>
       <span class="label">Messages:</span>
       <span class="value">{chatStore.messages.length}</span>
     </div>

     <button
       onclick={handleStartOver}
       disabled={chatStore.messages.length === 0}
       class="start-over"
     >
       Start Over
     </button>
   </div>

   <style>
     .session-info {
       display: flex;
       justify-content: space-between;
       align-items: center;
       padding: 0.75rem 1rem;
       background: #f9f9f9;
       border-radius: 4px;
       margin-bottom: 1rem;
       font-size: 0.875rem;
     }

     .info {
       display: flex;
       gap: 0.5rem;
       align-items: center;
       color: #666;
     }

     .label {
       font-weight: 500;
     }

     .separator {
       color: #ccc;
     }

     .start-over {
       padding: 0.5rem 1rem;
       border: none;
       border-radius: 4px;
       background: #ff5722;
       color: white;
       cursor: pointer;
       font-size: 0.875rem;
     }

     .start-over:hover:not(:disabled) {
       background: #e64a19;
     }

     .start-over:disabled {
       background: #ccc;
       cursor: not-allowed;
     }
   </style>
   ```

3. **Update main page with session info** (src/routes/+page.svelte)
   ```svelte
   <script>
     import { onMount } from 'svelte';
     import ChatHistory from '$lib/components/ChatHistory.svelte';
     import QueryForm from '$lib/components/QueryForm.svelte';
     import SessionInfo from '$lib/components/SessionInfo.svelte';
     import { chatStore } from '$lib/stores/chat.svelte';

     onMount(() => {
       chatStore.loadSession();
     });
   </script>

   <div class="page">
     <div class="header">
       <h1>FOIA Coach</h1>
       <a href="/settings">Settings</a>
     </div>

     <SessionInfo />
     <ChatHistory />
     <QueryForm />
   </div>

   <style>
     .page {
       max-width: 900px;
       margin: 0 auto;
       padding-bottom: 2rem;
     }

     .header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       margin-bottom: 1rem;
     }

     h1 {
       margin: 0;
     }
   </style>
   ```

4. **Update QueryForm to use context** (src/lib/components/QueryForm.svelte)
   ```svelte
   // Update the query submission to use chatStore.getContext()

   async function handleSubmit(event: Event) {
     event.preventDefault();

     if (!question.trim()) {
       return;
     }

     error = null;
     chatStore.setLoading(true);

     // Add user message
     chatStore.addMessage({
       role: 'user',
       content: question,
       state: selectedState || undefined,
     });

     try {
       // Get conversation context from store
       const context = chatStore.getContext();

       // Query API with context
       const response = await apiClient.query({
         question,
         state: selectedState || undefined,
         context,
       });

       // Add assistant response
       chatStore.addMessage({
         role: 'assistant',
         content: response.answer,
         citations: response.citations,
         state: response.state,
       });

       // Clear form
       question = '';
     } catch (e) {
       error = e.message;
       console.error('Query failed:', e);
     } finally {
       chatStore.setLoading(false);
     }
   }
   ```

5. **Test session persistence**
   - Start conversation
   - Ask several questions
   - Reload page - conversation should persist
   - Click "Start Over" - should clear and start fresh session

#### Deliverables

- [ ] Session management in chat store
- [ ] SessionInfo component created
- [ ] "Start Over" button works
- [ ] Context sent with each query
- [ ] Session persists on reload
- [ ] Session ID regenerated on "Start Over"

#### Success Criteria

```bash
npm run dev

# Browser test:
# 1. Visit http://localhost:5173
# 2. See session info bar (started time, 0 messages)
# 3. Ask a question - message count increases
# 4. Ask follow-up question - context maintained
# 5. Reload page - session and messages persist
# 6. Click "Start Over" button
# 7. Confirm dialog appears
# 8. Confirm - chat clears, new session ID
# 9. Session started time updates to current time
# 10. Ask new question - starts fresh context
```

---

### Phase 6: Polish & Integration Testing (30-45 minutes)

**Goal:** Final styling improvements, error handling polish, and end-to-end testing.

**Note:** Make it look good and ensure everything works together smoothly.

#### Tasks

1. **Add loading skeleton** (src/lib/components/LoadingSkeleton.svelte)
   ```svelte
   <div class="skeleton-message">
     <div class="skeleton-header">
       <div class="skeleton-line short"></div>
     </div>
     <div class="skeleton-content">
       <div class="skeleton-line"></div>
       <div class="skeleton-line"></div>
       <div class="skeleton-line medium"></div>
     </div>
   </div>

   <style>
     .skeleton-message {
       margin-bottom: 1.5rem;
       padding: 1rem;
       border-radius: 8px;
       background: #f5f5f5;
       max-width: 80%;
     }

     .skeleton-header {
       margin-bottom: 0.5rem;
     }

     .skeleton-line {
       height: 16px;
       background: linear-gradient(90deg, #e0e0e0 25%, #f0f0f0 50%, #e0e0e0 75%);
       background-size: 200% 100%;
       animation: loading 1.5s infinite;
       border-radius: 4px;
       margin-bottom: 0.5rem;
     }

     .skeleton-line.short {
       width: 30%;
     }

     .skeleton-line.medium {
       width: 70%;
     }

     @keyframes loading {
       0% {
         background-position: 200% 0;
       }
       100% {
         background-position: -200% 0;
       }
     }
   </style>
   ```

2. **Update ChatHistory with loading skeleton** (src/lib/components/ChatHistory.svelte)
   ```svelte
   <script lang="ts">
     import { chatStore } from '$lib/stores/chat.svelte';
     import ChatMessage from './ChatMessage.svelte';
     import LoadingSkeleton from './LoadingSkeleton.svelte';

     let chatContainer: HTMLDivElement;

     $effect(() => {
       if (chatStore.messages.length > 0 && chatContainer) {
         chatContainer.scrollTop = chatContainer.scrollHeight;
       }
     });
   </script>

   <div class="chat-history" bind:this={chatContainer}>
     {#if chatStore.messages.length === 0 && !chatStore.isLoading}
       <div class="empty-state">
         <h2>Welcome to FOIA Coach</h2>
         <p>Ask a question about state public records laws to get started.</p>
         <div class="examples">
           <p><strong>Example questions:</strong></p>
           <ul>
             <li>What is the response time for FOIA requests in Colorado?</li>
             <li>How do I appeal a denied records request in Georgia?</li>
             <li>What fees can agencies charge for public records?</li>
           </ul>
         </div>
       </div>
     {:else}
       {#each chatStore.messages as message (message.id)}
         <ChatMessage {message} />
       {/each}
     {/if}

     {#if chatStore.isLoading}
       <LoadingSkeleton />
     {/if}
   </div>

   <style>
     .chat-history {
       height: calc(100vh - 300px);
       min-height: 400px;
       overflow-y: auto;
       padding: 1rem;
       border: 1px solid #ddd;
       border-radius: 8px;
       background: white;
     }

     .empty-state {
       display: flex;
       flex-direction: column;
       align-items: center;
       justify-content: center;
       height: 100%;
       text-align: center;
       color: #666;
       padding: 2rem;
     }

     .empty-state h2 {
       margin: 0 0 0.5rem 0;
       color: #333;
     }

     .empty-state p {
       margin: 0 0 1rem 0;
     }

     .examples {
       text-align: left;
       max-width: 500px;
     }

     .examples ul {
       margin: 0.5rem 0;
       padding-left: 1.5rem;
     }

     .examples li {
       margin-bottom: 0.5rem;
       color: #666;
       font-style: italic;
     }
   </style>
   ```

3. **Add keyboard shortcuts** (src/routes/+page.svelte)
   ```svelte
   <script>
     import { onMount } from 'svelte';
     import ChatHistory from '$lib/components/ChatHistory.svelte';
     import QueryForm from '$lib/components/QueryForm.svelte';
     import SessionInfo from '$lib/components/SessionInfo.svelte';
     import { chatStore } from '$lib/stores/chat.svelte';

     onMount(() => {
       chatStore.loadSession();

       // Keyboard shortcuts
       function handleKeyboard(e: KeyboardEvent) {
         // Cmd/Ctrl + K = Clear chat
         if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
           e.preventDefault();
           chatStore.startOver();
         }
       }

       window.addEventListener('keydown', handleKeyboard);

       return () => {
         window.removeEventListener('keydown', handleKeyboard);
       };
     });
   </script>

   <div class="page">
     <div class="header">
       <h1>FOIA Coach</h1>
       <div class="header-actions">
         <a href="/settings" class="settings-link">Settings</a>
       </div>
     </div>

     <SessionInfo />
     <ChatHistory />
     <QueryForm />

     <div class="footer">
       <small>
         Tip: Press <kbd>Cmd+K</kbd> (Mac) or <kbd>Ctrl+K</kbd> (Windows) to start over
       </small>
     </div>
   </div>

   <style>
     .page {
       max-width: 900px;
       margin: 0 auto;
       padding-bottom: 2rem;
     }

     .header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       margin-bottom: 1rem;
     }

     h1 {
       margin: 0;
     }

     .settings-link {
       padding: 0.5rem 1rem;
       background: #f0f0f0;
       border-radius: 4px;
       color: #333;
       text-decoration: none;
     }

     .settings-link:hover {
       background: #e0e0e0;
     }

     .footer {
       margin-top: 1rem;
       text-align: center;
       color: #999;
     }

     kbd {
       padding: 0.125rem 0.375rem;
       background: #f0f0f0;
       border: 1px solid #ccc;
       border-radius: 3px;
       font-family: monospace;
       font-size: 0.875em;
     }
   </style>
   ```

4. **Add better error handling** (src/lib/api/client.ts)
   ```typescript
   // Update error handling in APIClient

   async query(request: QueryRequest): Promise<QueryResponse> {
     try {
       const response = await fetch(`${this.getBaseUrl()}/api/v1/query/query/`, {
         method: 'POST',
         headers: this.getHeaders(),
         body: JSON.stringify(request),
       });

       if (!response.ok) {
         let errorMessage = `API error: ${response.status} ${response.statusText}`;

         try {
           const errorData = await response.json();
           if (errorData.detail) {
             errorMessage = errorData.detail;
           } else if (errorData.error) {
             errorMessage = errorData.error;
           }
         } catch (e) {
           // JSON parsing failed, use default error message
         }

         throw new Error(errorMessage);
       }

       return response.json();
     } catch (e) {
       if (e instanceof TypeError && e.message.includes('fetch')) {
         throw new Error('Cannot connect to API. Check your settings and ensure the API is running.');
       }
       throw e;
     }
   }
   ```

5. **Create comprehensive README** (foia-coach-ui/README.md)
   ```markdown
   # FOIA Coach UI

   Simple SvelteKit interface for the FOIA Coach API.

   ## Setup

   ```bash
   npm install
   npm run dev
   ```

   Visit http://localhost:5173

   ## Features

   - Chat interface for querying Gemini about state public records laws
   - Conversation context maintained across questions
   - State-specific queries
   - Settings management (API URL, authentication)
   - Session persistence
   - "Start Over" to begin new conversation

   ## Configuration

   Visit http://localhost:5173/settings to configure:

   - **API URL**: Base URL for FOIA Coach API (default: http://localhost:8001)
   - **API Token**: Optional authentication token for remote access
   - **Gemini Model**: Model identifier (informational only)

   ## Usage

   1. Configure settings (if not using defaults)
   2. Test connection to API
   3. Start asking questions!
   4. Use state selector for state-specific queries
   5. Click "Start Over" to clear context and begin fresh

   ## Keyboard Shortcuts

   - `Cmd+K` / `Ctrl+K` - Start over (clear chat)

   ## Requirements

   - FOIA Coach API running on port 8001
   - Modern browser with JavaScript enabled
   ```

6. **End-to-end testing checklist**
   - [ ] Settings persist across reloads
   - [ ] Can connect to API
   - [ ] Can submit questions
   - [ ] Responses display correctly
   - [ ] Citations render properly
   - [ ] Loading states work
   - [ ] Error messages display
   - [ ] Session persists on reload
   - [ ] "Start Over" clears context
   - [ ] State selector works
   - [ ] Keyboard shortcuts work

#### Deliverables

- [ ] Loading skeleton added
- [ ] Better empty state with examples
- [ ] Keyboard shortcuts implemented
- [ ] Improved error handling
- [ ] README documentation
- [ ] All features tested end-to-end

#### Success Criteria

```bash
# Full integration test

# 1. Start API
docker compose -f local.yml up foia_coach_api

# 2. Start UI
cd foia-coach-ui
npm run dev

# 3. Browser testing:
# - Visit http://localhost:5173/settings
# - Test connection - should succeed
# - Visit http://localhost:5173
# - See welcome message with examples
# - Select "Colorado" from dropdown
# - Ask: "What is the response time?"
# - See loading skeleton
# - See response with answer and citations
# - Ask follow-up: "What if they don't respond?"
# - Context should be maintained (follow-up understood)
# - Reload page - conversation persists
# - Press Cmd+K - confirm and start over
# - Session clears, ready for new conversation
# - Stop API (docker compose down)
# - Try to submit question
# - See clear error message about connection
```

---

## Configuration Reference

### Environment

No environment variables needed for development. All configuration is through the Settings UI.

### Default Settings

```typescript
{
  apiUrl: 'http://localhost:8001',
  apiToken: '',
  geminiModel: 'gemini-2.0-flash-001'
}
```

### LocalStorage Keys

- `foia-coach-settings` - User settings (API URL, token, model)
- `foia-coach-session` - Current chat session (messages, session ID)

---

## NPM Scripts

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint

# Format
npm run format
```

---

## Success Metrics

### Technical Success
- ✅ SvelteKit project builds and runs
- ✅ All components render correctly
- ✅ API client handles requests/errors
- ✅ LocalStorage persistence works
- ✅ Context accumulation working

### Functional Success
- ✅ Can configure API settings
- ✅ Can submit questions and get responses
- ✅ Citations display correctly
- ✅ Conversation context maintained
- ✅ "Start Over" clears context
- ✅ Session persists across reloads

### UX Success
- ✅ Clean, simple interface
- ✅ Loading states provide feedback
- ✅ Error messages are clear
- ✅ Keyboard shortcuts work
- ✅ Responsive layout

---

## Next Steps After Phase 6

Once this UI is complete:

1. **Load Real Data** - Add jurisdiction resources for CO, GA, TN to API
2. **Test Quality** - Evaluate Gemini responses with real questions
3. **Gather Feedback** - Share with team for user testing
4. **Iterate** - Improve based on usage patterns
5. **Future Features:**
   - Add more states beyond CO, GA, TN
   - Export conversation
   - Share queries
   - Better citation formatting
   - Mobile responsive design
   - Dark mode

---

## Troubleshooting

### API Connection Issues

**Problem:** "Cannot connect to API"
**Solution:**
1. Check FOIA Coach API is running: `docker compose -f local.yml ps`
2. Verify API URL in settings: http://localhost:8001
3. Test API directly: `curl http://localhost:8001/api/v1/jurisdictions/`

### CORS Errors

**Problem:** CORS error in browser console
**Solution:**
1. Verify CORS is configured in API settings
2. Check ALLOWED_ORIGINS includes http://localhost:5173
3. Restart API after settings changes

### Session Not Persisting

**Problem:** Chat clears on reload
**Solution:**
1. Check browser localStorage is enabled
2. Open DevTools > Application > Local Storage
3. Verify `foia-coach-session` key exists

### Build Errors

**Problem:** TypeScript errors during build
**Solution:**
1. Ensure all types are properly imported
2. Run `npm run check` inside container: `docker compose -f local.yml exec foia_coach_ui npm run check`
3. Add `// @ts-ignore` for problematic lines (temporary)

### Docker Container Issues

**Problem:** Container won't start or build fails
**Solution:**
1. Check logs: `docker compose -f local.yml logs foia_coach_ui --tail=100`
2. Rebuild container: `docker compose -f local.yml build --no-cache foia_coach_ui`
3. Remove and recreate: `docker compose -f local.yml down && docker compose -f local.yml up foia_coach_ui -d`

**Problem:** `@types/node` version conflict during build
**Solution:**
1. Verify `foia-coach-ui/package.json` has `@types/node@^20.19.0` (not ^18)
2. Rebuild container after fixing: `docker compose -f local.yml build foia_coach_ui`

**Problem:** Code changes not reflecting in browser
**Solution:**
1. Vite hot reload should work automatically with volume mount
2. If not working, check volume mount in `local.yml`: `- ./foia-coach-ui:/app:z`
3. Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
4. Restart container if needed: `docker compose -f local.yml restart foia_coach_ui`

---

## Architecture Decisions

### Why Docker?
- **Node version isolation**: Main MuckRock project uses Node 18, but Vite 7 requires Node 20+
- **Consistent environment**: Same setup for all developers
- **No local Node conflicts**: Avoids `@types/node` version conflicts with parent project
- **Easy cleanup**: Can remove entire container without affecting host system
- **Production-ready**: Same containerization strategy as other services (foia_coach_api)

### Why Svelte 5?
- Latest version with improved reactivity (runes)
- Simpler than React for small projects
- Excellent developer experience
- Fast runtime performance

### Why No Component Library?
- Keep it simple for experimental phase
- Custom CSS gives full control
- No extra dependencies to manage
- Easy to add later if needed

### Why LocalStorage?
- No backend database needed
- Simple persistence
- Good enough for single-user experimental tool
- Easy to upgrade to server-side storage later

### Why Native Fetch?
- No external HTTP library needed
- Built into all modern browsers
- Sufficient for our simple API needs
- TypeScript types available

---

## Estimated Timeline

| Phase | Tasks | Time Estimate | Complexity |
|-------|-------|---------------|------------|
| Phase 1 | SvelteKit scaffold | 30-45 min | Low |
| Phase 2 | API client + settings | 45-60 min | Medium |
| Phase 3 | Chat UI components | 45-60 min | Medium |
| Phase 4 | Query form + API integration | 45-60 min | Medium |
| Phase 5 | Context management | 30-45 min | Low |
| Phase 6 | Polish + testing | 30-45 min | Low |
| **Total** | | **4-6 hours** | |

**Smaller phases for:**
- Clear progress tracking
- Easy rollback if needed
- Frequent working checkpoints
- Better session management
