# Web Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a web frontend that lets users enter a URL, see real-time crawling progress via SSE, view the resulting markdown, and download it as a `.md` file.

**Architecture:** Single-page React app in `frontend/` directory. Communicates with the existing FastAPI backend at `http://localhost:8000/api/v1`. No routing needed — one page with stateful transitions (idle → submitting → processing → completed/error).

**Tech Stack:** React 18, Vite, TypeScript, react-markdown, CSS Modules

---

### Task 1: Scaffold Vite + React + TypeScript project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/App.module.css`
- Create: `frontend/src/vite-env.d.ts`

**Step 1: Create project with Vite**

```bash
cd /Users/donghun2/workspace/Site-Clipper
npm create vite@latest frontend -- --template react-ts
```

**Step 2: Install dependencies**

```bash
cd /Users/donghun2/workspace/Site-Clipper/frontend
npm install
npm install react-markdown
```

**Step 3: Configure Vite proxy to backend**

Edit `frontend/vite.config.ts`:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

**Step 4: Verify dev server starts**

```bash
cd /Users/donghun2/workspace/Site-Clipper/frontend
npm run dev
```

Expected: Vite dev server running on http://localhost:5173

**Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold web frontend with Vite + React + TypeScript"
```

---

### Task 2: API client and types

**Files:**
- Create: `frontend/src/api/types.ts`
- Create: `frontend/src/api/client.ts`

**Step 1: Define TypeScript types matching backend models**

`frontend/src/api/types.ts`:

```ts
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface CrawlRequest {
  url: string;
  sitemap: boolean;
}

export interface CrawlResponse {
  task_id: string;
  status: TaskStatus;
}

export interface TaskResult {
  id: string;
  url: string;
  status: TaskStatus;
  progress: number;
  total_pages: number;
  processed_pages: number;
  result: string | null;
  error: string | null;
}

export interface SseProgressEvent {
  status: TaskStatus;
  progress: number;
  total_pages: number;
  processed_pages: number;
}

export interface SseDoneEvent {
  status: TaskStatus;
  progress: number;
  result: string | null;
  error: string | null;
}
```

**Step 2: Implement API client with SSE support**

`frontend/src/api/client.ts`:

```ts
import { CrawlRequest, CrawlResponse, SseDoneEvent, SseProgressEvent, TaskResult } from './types';

const BASE = '/api/v1';

export async function submitCrawl(req: CrawlRequest): Promise<CrawlResponse> {
  const res = await fetch(`${BASE}/crawl`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Submit failed: ${res.status}`);
  return res.json();
}

export async function getTask(taskId: string): Promise<TaskResult> {
  const res = await fetch(`${BASE}/tasks/${taskId}`);
  if (!res.ok) throw new Error(`Get task failed: ${res.status}`);
  return res.json();
}

export function streamTask(
  taskId: string,
  onProgress: (data: SseProgressEvent) => void,
  onDone: (data: SseDoneEvent) => void,
  onError: (err: Error) => void,
): () => void {
  const es = new EventSource(`${BASE}/tasks/${taskId}/stream`);

  es.addEventListener('progress', (e) => {
    onProgress(JSON.parse(e.data));
  });

  es.addEventListener('done', (e) => {
    onDone(JSON.parse(e.data));
    es.close();
  });

  es.onerror = () => {
    es.close();
    onError(new Error('SSE connection failed'));
  };

  return () => es.close();
}
```

**Step 3: Commit**

```bash
git add frontend/src/api/
git commit -m "feat: add API client with SSE streaming support"
```

---

### Task 3: Main App component with state machine

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.module.css`

**Step 1: Implement App with state transitions**

`frontend/src/App.tsx`:

```tsx
import { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { submitCrawl, streamTask, getTask } from './api/client';
import { TaskStatus, SseProgressEvent } from './api/types';
import styles from './App.module.css';

type AppState =
  | { phase: 'idle' }
  | { phase: 'submitting' }
  | { phase: 'processing'; taskId: string; progress: number; totalPages: number; processedPages: number }
  | { phase: 'completed'; markdown: string; url: string }
  | { phase: 'error'; message: string };

export default function App() {
  const [url, setUrl] = useState('');
  const [sitemap, setSitemap] = useState(false);
  const [state, setState] = useState<AppState>({ phase: 'idle' });
  const [viewRaw, setViewRaw] = useState(false);

  const handleSubmit = useCallback(async () => {
    if (!url.trim()) return;

    setState({ phase: 'submitting' });

    try {
      const { task_id } = await submitCrawl({ url: url.trim(), sitemap });

      setState({ phase: 'processing', taskId: task_id, progress: 0, totalPages: 0, processedPages: 0 });

      const cleanup = streamTask(
        task_id,
        (data: SseProgressEvent) => {
          setState({
            phase: 'processing',
            taskId: task_id,
            progress: data.progress,
            totalPages: data.total_pages,
            processedPages: data.processed_pages,
          });
        },
        (data) => {
          if (data.status === 'completed' && data.result) {
            setState({ phase: 'completed', markdown: data.result, url: url.trim() });
          } else {
            setState({ phase: 'error', message: data.error || 'Unknown error' });
          }
        },
        async () => {
          // SSE failed — fallback to polling
          const poll = async () => {
            const task = await getTask(task_id);
            if (task.status === 'completed' && task.result) {
              setState({ phase: 'completed', markdown: task.result, url: url.trim() });
            } else if (task.status === 'failed') {
              setState({ phase: 'error', message: task.error || 'Crawl failed' });
            } else {
              setState({
                phase: 'processing',
                taskId: task_id,
                progress: task.progress,
                totalPages: task.total_pages,
                processedPages: task.processed_pages,
              });
              setTimeout(poll, 2000);
            }
          };
          poll();
        },
      );

      // cleanup stored but not used in MVP — browser handles on unmount
      void cleanup;
    } catch (err) {
      setState({ phase: 'error', message: err instanceof Error ? err.message : 'Request failed' });
    }
  }, [url, sitemap]);

  const handleDownload = useCallback(() => {
    if (state.phase !== 'completed') return;
    const blob = new Blob([state.markdown], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    const filename = state.url
      .replace(/^https?:\/\//, '')
      .replace(/[/\\?%*:|"<>]/g, '_')
      .slice(0, 80) + '.md';
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }, [state]);

  const handleReset = useCallback(() => {
    setState({ phase: 'idle' });
    setUrl('');
    setSitemap(false);
    setViewRaw(false);
  }, []);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Site Clipper</h1>
        <p>URL to Markdown converter</p>
      </header>

      <main className={styles.main}>
        {/* URL Input */}
        {(state.phase === 'idle' || state.phase === 'error') && (
          <div className={styles.inputSection}>
            <div className={styles.inputRow}>
              <input
                type="url"
                className={styles.urlInput}
                placeholder="https://example.com/docs"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              />
              <button
                className={styles.submitBtn}
                onClick={handleSubmit}
                disabled={!url.trim()}
              >
                Convert
              </button>
            </div>
            <label className={styles.sitemapToggle}>
              <input
                type="checkbox"
                checked={sitemap}
                onChange={(e) => setSitemap(e.target.checked)}
              />
              Crawl entire sitemap
            </label>
            {state.phase === 'error' && (
              <p className={styles.errorText}>{state.message}</p>
            )}
          </div>
        )}

        {/* Submitting */}
        {state.phase === 'submitting' && (
          <div className={styles.statusSection}>
            <div className={styles.spinner} />
            <p>Submitting...</p>
          </div>
        )}

        {/* Processing */}
        {state.phase === 'processing' && (
          <div className={styles.statusSection}>
            <div className={styles.progressContainer}>
              <div className={styles.progressBar} style={{ width: `${state.progress}%` }} />
            </div>
            <p>
              {state.progress > 0
                ? `Processing... ${state.progress}% (${state.processedPages}/${state.totalPages} pages)`
                : 'Starting crawl...'}
            </p>
          </div>
        )}

        {/* Completed */}
        {state.phase === 'completed' && (
          <div className={styles.resultSection}>
            <div className={styles.resultToolbar}>
              <button className={styles.downloadBtn} onClick={handleDownload}>
                Download .md
              </button>
              <button
                className={styles.toggleBtn}
                onClick={() => setViewRaw(!viewRaw)}
              >
                {viewRaw ? 'Rendered' : 'Raw'}
              </button>
              <button className={styles.resetBtn} onClick={handleReset}>
                New URL
              </button>
            </div>
            <div className={styles.markdownViewer}>
              {viewRaw ? (
                <pre className={styles.rawMarkdown}>{state.markdown}</pre>
              ) : (
                <div className={styles.renderedMarkdown}>
                  <ReactMarkdown>{state.markdown}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
```

**Step 2: Add styles**

`frontend/src/App.module.css`:

```css
.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #1a1a1a;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.header h1 {
  margin: 0;
  font-size: 1.8rem;
}

.header p {
  margin: 0.25rem 0 0;
  color: #666;
}

.main {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Input Section */
.inputSection {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.inputRow {
  display: flex;
  gap: 0.5rem;
}

.urlInput {
  flex: 1;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  outline: none;
  transition: border-color 0.2s;
}

.urlInput:focus {
  border-color: #2563eb;
}

.submitBtn {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.submitBtn:hover:not(:disabled) {
  background: #1d4ed8;
}

.submitBtn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sitemapToggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #555;
  cursor: pointer;
}

.errorText {
  color: #dc2626;
  font-size: 0.9rem;
  margin: 0;
}

/* Status Section */
.statusSection {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progressContainer {
  width: 100%;
  max-width: 400px;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progressBar {
  height: 100%;
  background: #2563eb;
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* Result Section */
.resultSection {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.resultToolbar {
  display: flex;
  gap: 0.5rem;
}

.downloadBtn,
.toggleBtn,
.resetBtn {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  font-weight: 500;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  background: #fff;
  transition: background 0.2s;
}

.downloadBtn {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.downloadBtn:hover {
  background: #1d4ed8;
}

.toggleBtn:hover,
.resetBtn:hover {
  background: #f3f4f6;
}

.markdownViewer {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  background: #fff;
  max-height: 70vh;
  overflow-y: auto;
}

.rawMarkdown {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.85rem;
  line-height: 1.6;
}

.renderedMarkdown h1,
.renderedMarkdown h2,
.renderedMarkdown h3 {
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}

.renderedMarkdown p {
  line-height: 1.7;
}

.renderedMarkdown code {
  background: #f3f4f6;
  padding: 0.15rem 0.3rem;
  border-radius: 3px;
  font-size: 0.85em;
}

.renderedMarkdown pre {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
}

.renderedMarkdown pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.renderedMarkdown a {
  color: #2563eb;
}

.renderedMarkdown blockquote {
  border-left: 3px solid #e5e7eb;
  margin-left: 0;
  padding-left: 1rem;
  color: #666;
}
```

**Step 3: Clean up default Vite boilerplate**

Remove `frontend/src/App.css`, `frontend/src/index.css` (if any default content exists), update `frontend/src/main.tsx` to be minimal:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

**Step 4: Verify the app renders**

```bash
cd /Users/donghun2/workspace/Site-Clipper/frontend
npm run dev
```

Open http://localhost:5173 in browser. Should show "Site Clipper" header with URL input.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: implement main App with URL input, SSE progress, markdown viewer"
```

---

### Task 4: Update index.html and add global reset

**Files:**
- Modify: `frontend/index.html`

**Step 1: Update index.html title and add minimal global styles**

`frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Site Clipper</title>
    <style>
      *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
      body { background: #fafafa; min-height: 100vh; }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "feat: update index.html with title and global reset"
```

---

### Task 5: End-to-end verification

**Step 1: Start backend**

```bash
cd /Users/donghun2/workspace/Site-Clipper/backend
# Ensure backend is running on port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Step 2: Start frontend**

```bash
cd /Users/donghun2/workspace/Site-Clipper/frontend
npm run dev
```

**Step 3: Test full flow**

1. Open http://localhost:5173
2. Enter a URL (e.g., `https://example.com`)
3. Click "Convert"
4. Verify progress bar appears
5. Verify markdown renders on completion
6. Click "Download .md" — verify file downloads
7. Click "Raw" — verify raw markdown shows
8. Click "New URL" — verify reset

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete web frontend MVP"
```
