export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type CrawlMode = 'single' | 'sitemap' | 'smart';

export interface CrawlRequest {
  url: string;
  mode: CrawlMode;
  sitemap?: boolean;  // Legacy field
  path_prefix?: string;
  max_pages?: number;
  gemini_api_key?: string;
  gemini_model?: string;
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
