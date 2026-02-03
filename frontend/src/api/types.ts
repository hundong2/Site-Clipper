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
