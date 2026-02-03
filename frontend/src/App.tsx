import { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { submitCrawl, streamTask, getTask } from './api/client';
import type { CrawlMode, SseProgressEvent } from './api/types';
import styles from './App.module.css';

type AppState =
  | { phase: 'idle' }
  | { phase: 'submitting' }
  | { phase: 'processing'; taskId: string; progress: number; totalPages: number; processedPages: number }
  | { phase: 'completed'; markdown: string; url: string }
  | { phase: 'error'; message: string };

export default function App() {
  const [url, setUrl] = useState('');
  const [mode, setMode] = useState<CrawlMode>('single');
  const [maxPages, setMaxPages] = useState(50);
  const [state, setState] = useState<AppState>({ phase: 'idle' });
  const [viewRaw, setViewRaw] = useState(false);

  const handleSubmit = useCallback(async () => {
    if (!url.trim()) return;

    setState({ phase: 'submitting' });

    try {
      const { task_id } = await submitCrawl({
        url: url.trim(),
        mode,
        max_pages: mode === 'smart' ? maxPages : undefined,
      });

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

      void cleanup;
    } catch (err) {
      setState({ phase: 'error', message: err instanceof Error ? err.message : 'Request failed' });
    }
  }, [url, mode, maxPages]);

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
    setMode('single');
    setMaxPages(50);
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

            {/* Mode Selection */}
            <div className={styles.modeSection}>
              <label className={styles.modeLabel}>
                <input
                  type="radio"
                  name="mode"
                  value="single"
                  checked={mode === 'single'}
                  onChange={() => setMode('single')}
                />
                Single page
              </label>
              <label className={styles.modeLabel}>
                <input
                  type="radio"
                  name="mode"
                  value="sitemap"
                  checked={mode === 'sitemap'}
                  onChange={() => setMode('sitemap')}
                />
                Sitemap
              </label>
              <label className={styles.modeLabel}>
                <input
                  type="radio"
                  name="mode"
                  value="smart"
                  checked={mode === 'smart'}
                  onChange={() => setMode('smart')}
                />
                Smart (AI)
              </label>
            </div>

            {/* Smart Mode Options */}
            {mode === 'smart' && (
              <div className={styles.smartOptions}>
                <label className={styles.optionLabel}>
                  Max pages:
                  <input
                    type="number"
                    min={1}
                    max={200}
                    value={maxPages}
                    onChange={(e) => setMaxPages(Number(e.target.value))}
                    className={styles.numberInput}
                  />
                </label>
                <p className={styles.smartHint}>
                  AI will analyze navigation links (Next, Menu, TOC) to crawl documentation.
                </p>
              </div>
            )}

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
