import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable


logger = logging.getLogger(__name__)


class JobQueue(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def enqueue(self, job_id: str) -> None:
        raise NotImplementedError


class AsyncioWorkerQueue(JobQueue):
    def __init__(
        self,
        worker_func: Callable[[str], Awaitable[None]],
        concurrency: int = 2,
    ) -> None:
        self.worker_func = worker_func
        self.concurrency = concurrency
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []
        self._running = False

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._workers = [
            asyncio.create_task(
                self._worker_loop(f"video-worker-{index}"),
                name=f"video-worker-{index}",
            )
            for index in range(self.concurrency)
        ]
        logger.info(
            "AsyncioWorkerQueue started with %d concurrent workers",
            self.concurrency,
        )

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        workers = list(self._workers)
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        self._workers.clear()
        logger.info("AsyncioWorkerQueue stopped gracefully")

    async def enqueue(self, job_id: str) -> None:
        await self.queue.put(job_id)
        logger.info("Job %s enqueued; queue size=%d", job_id, self.queue.qsize())

    async def _worker_loop(self, worker_name: str) -> None:
        while self._running:
            try:
                job_id = await self.queue.get()
                try:
                    await self.worker_func(job_id)
                except Exception:
                    logger.exception(
                        "[%s] Unhandled error processing job %s",
                        worker_name,
                        job_id,
                    )
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("[%s] Worker loop error", worker_name)
