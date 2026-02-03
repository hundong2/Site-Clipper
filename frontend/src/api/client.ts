import type { CrawlRequest, CrawlResponse, SseDoneEvent, SseProgressEvent, TaskResult } from './types';

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
    onProgress(JSON.parse((e as MessageEvent).data));
  });

  es.addEventListener('done', (e) => {
    onDone(JSON.parse((e as MessageEvent).data));
    es.close();
  });

  es.onerror = () => {
    es.close();
    onError(new Error('SSE connection failed'));
  };

  return () => es.close();
}
