import asyncio
import json

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.api.models import (
    CrawlMode,
    CrawlRequest,
    CrawlResponse,
    DriveUploadRequest,
    DriveUploadResponse,
    HealthResponse,
    TaskResult,
    TaskStatus,
)
from app.services.gdrive_service import upload_to_drive
from app.services.task_service import task_store
from app.workers.crawl_worker import run_crawl_task

router = APIRouter(prefix="/api/v1")


@router.post("/crawl", response_model=CrawlResponse)
async def create_crawl(req: CrawlRequest, bg: BackgroundTasks):
    task = task_store.create(str(req.url))
    cookies = [c.model_dump() for c in req.cookies] if req.cookies else None

    # Determine mode: use explicit mode, or legacy sitemap field
    mode = req.mode
    if mode == CrawlMode.SINGLE and req.sitemap:
        mode = CrawlMode.SITEMAP

    bg.add_task(
        run_crawl_task,
        task_id=task.id,
        url=str(req.url),
        mode=mode,
        cookies=cookies,
        path_prefix=req.path_prefix,
        max_pages=req.max_pages,
        gemini_api_key=req.gemini_api_key,
        gemini_model=req.gemini_model,
    )
    return CrawlResponse(task_id=task.id, status=TaskStatus.PENDING)


@router.get("/tasks/{task_id}", response_model=TaskResult)
async def get_task(task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResult(
        id=task.id,
        url=task.url,
        status=task.status,
        progress=task.progress,
        total_pages=task.total_pages,
        processed_pages=task.processed_pages,
        result=task.result,
        error=task.error,
    )


@router.get("/tasks/{task_id}/stream")
async def stream_task(task_id: str, request: Request):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        event = task_store.subscribe(task_id)
        try:
            while True:
                if await request.is_disconnected():
                    break

                t = task_store.get(task_id)
                if not t:
                    break

                data = json.dumps({
                    "status": t.status.value,
                    "progress": t.progress,
                    "total_pages": t.total_pages,
                    "processed_pages": t.processed_pages,
                })
                yield {"event": "progress", "data": data}

                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    final = json.dumps({
                        "status": t.status.value,
                        "progress": t.progress,
                        "result": t.result if t.status == TaskStatus.COMPLETED else None,
                        "error": t.error if t.status == TaskStatus.FAILED else None,
                    })
                    yield {"event": "done", "data": final}
                    break

                # Wait for next update notification
                event.clear()
                try:
                    await asyncio.wait_for(event.wait(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"event": "ping", "data": ""}
        finally:
            task_store.unsubscribe(task_id, event)

    return EventSourceResponse(event_generator())


@router.post("/drive/upload", response_model=DriveUploadResponse)
async def drive_upload(req: DriveUploadRequest):
    task = task_store.get(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.COMPLETED or not task.result:
        raise HTTPException(status_code=400, detail="Task not completed")

    filename = req.filename
    if not filename:
        filename = (
            task.url.replace("https://", "")
            .replace("http://", "")
            .replace("/", "_")[:80]
            + ".md"
        )

    result = upload_to_drive(
        access_token=req.access_token,
        filename=filename,
        content=task.result,
    )
    return DriveUploadResponse(**result)


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()
