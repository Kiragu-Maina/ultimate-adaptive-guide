"""
Asynchronous Job Queue System using Redis

Handles long-running tasks asynchronously:
1. Client submits job → Returns 202 Accepted with job_id
2. Worker processes job in background
3. Client polls status endpoint with job_id
4. Once complete, client fetches result

Jobs are stored in Redis with status tracking:
- pending: Job is queued but not started
- processing: Job is currently being processed
- completed: Job finished successfully
- failed: Job encountered an error
"""

import uuid
import json
import time
import traceback
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import threading
from cache_redis import redis_client, is_redis_available


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobQueue:
    """Redis-based job queue for async task processing"""

    JOB_PREFIX = "job:"
    QUEUE_KEY = "job_queue"
    WORKER_ACTIVE = "worker_active"

    @staticmethod
    def create_job(job_type: str, params: Dict[str, Any]) -> str:
        """
        Create a new job and add it to the queue

        Args:
            job_type: Type of job (e.g., "onboarding", "content_generation")
            params: Job parameters

        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())

        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "status": JobStatus.PENDING,
            "params": params,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "result": None,
            "error": None
        }

        # Store job data
        key = f"{JobQueue.JOB_PREFIX}{job_id}"
        redis_client.setex(
            key,
            3600,  # TTL: 1 hour
            json.dumps(job_data)
        )

        # Add to queue
        redis_client.rpush(JobQueue.QUEUE_KEY, job_id)

        print(f"✨ Created job {job_id} of type {job_type}")
        return job_id

    @staticmethod
    def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current job status

        Args:
            job_id: Job identifier

        Returns:
            Job data or None if not found
        """
        key = f"{JobQueue.JOB_PREFIX}{job_id}"
        data = redis_client.get(key)

        if data:
            return json.loads(data)
        return None

    @staticmethod
    def update_job(job_id: str, updates: Dict[str, Any]):
        """
        Update job data

        Args:
            job_id: Job identifier
            updates: Dictionary of fields to update
        """
        key = f"{JobQueue.JOB_PREFIX}{job_id}"
        job_data = JobQueue.get_job_status(job_id)

        if job_data:
            job_data.update(updates)
            job_data["updated_at"] = datetime.utcnow().isoformat()

            redis_client.setex(
                key,
                3600,  # Extend TTL
                json.dumps(job_data)
            )

    @staticmethod
    def set_job_processing(job_id: str):
        """Mark job as processing"""
        JobQueue.update_job(job_id, {
            "status": JobStatus.PROCESSING,
            "started_at": datetime.utcnow().isoformat()
        })

    @staticmethod
    def set_job_completed(job_id: str, result: Any):
        """Mark job as completed with result"""
        JobQueue.update_job(job_id, {
            "status": JobStatus.COMPLETED,
            "result": result,
            "progress": 100,
            "completed_at": datetime.utcnow().isoformat()
        })

    @staticmethod
    def set_job_failed(job_id: str, error: str):
        """Mark job as failed with error"""
        JobQueue.update_job(job_id, {
            "status": JobStatus.FAILED,
            "error": error,
            "failed_at": datetime.utcnow().isoformat()
        })

    @staticmethod
    def update_job_progress(job_id: str, progress: int, message: str = ""):
        """Update job progress (0-100)"""
        JobQueue.update_job(job_id, {
            "progress": progress,
            "progress_message": message
        })

    @staticmethod
    def get_next_job() -> Optional[str]:
        """
        Get next job from queue (blocking with timeout)

        Returns:
            job_id or None if queue is empty
        """
        result = redis_client.blpop(JobQueue.QUEUE_KEY, timeout=1)
        if result:
            _, job_id = result
            return job_id.decode() if isinstance(job_id, bytes) else job_id
        return None


# Job processor registry
JOB_PROCESSORS: Dict[str, Callable] = {}


def register_job_processor(job_type: str):
    """
    Decorator to register a job processor function

    Example:
        @register_job_processor("onboarding")
        def process_onboarding(params):
            # Process onboarding
            return result
    """
    def decorator(func: Callable):
        JOB_PROCESSORS[job_type] = func
        print(f"📝 Registered job processor: {job_type}")
        return func
    return decorator


class JobWorker:
    """Background worker that processes jobs from the queue"""

    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        """Start the worker in a background thread"""
        if self.running:
            print("⚠️  Worker already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        print("🚀 Job worker started")

    def stop(self):
        """Stop the worker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 Job worker stopped")

    def _worker_loop(self):
        """Main worker loop - processes jobs from queue"""
        print("👷 Worker loop started")

        while self.running:
            try:
                # Check if Redis is available
                if not is_redis_available():
                    print("⚠️  Redis not available, waiting...")
                    time.sleep(5)
                    continue

                # Get next job
                job_id = JobQueue.get_next_job()

                if not job_id:
                    continue

                # Process job
                self._process_job(job_id)

            except Exception as e:
                print(f"❌ Worker error: {e}")
                traceback.print_exc()
                time.sleep(1)

    def _process_job(self, job_id: str):
        """Process a single job"""
        try:
            print(f"\n{'='*60}")
            print(f"🔨 Processing job: {job_id}")
            print(f"{'='*60}")

            # Get job data
            job_data = JobQueue.get_job_status(job_id)
            if not job_data:
                print(f"❌ Job {job_id} not found")
                return

            job_type = job_data["job_type"]
            params = job_data["params"]

            # Mark as processing
            JobQueue.set_job_processing(job_id)

            # Get processor
            processor = JOB_PROCESSORS.get(job_type)
            if not processor:
                error = f"No processor registered for job type: {job_type}"
                print(f"❌ {error}")
                JobQueue.set_job_failed(job_id, error)
                return

            # Process job
            print(f"🎯 Running processor for {job_type}")
            result = processor(params, job_id)

            # Mark as completed
            JobQueue.set_job_completed(job_id, result)
            print(f"✅ Job {job_id} completed successfully")

        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            print(f"❌ Job {job_id} failed: {error}")
            traceback.print_exc()
            JobQueue.set_job_failed(job_id, error)


# Global worker instance
_worker = None


def start_job_worker():
    """Start the global job worker"""
    global _worker
    if _worker is None:
        _worker = JobWorker()
    _worker.start()


def stop_job_worker():
    """Stop the global job worker"""
    global _worker
    if _worker:
        _worker.stop()


if __name__ == "__main__":
    # Test job queue
    print("Testing job queue system...")

    if not is_redis_available():
        print("❌ Redis not available")
        exit(1)

    # Register test processor
    @register_job_processor("test")
    def test_processor(params, job_id):
        print(f"Processing test job with params: {params}")

        # Simulate work with progress updates
        for i in range(5):
            time.sleep(1)
            JobQueue.update_job_progress(job_id, (i + 1) * 20, f"Step {i+1}/5")

        return {"message": "Test completed", "input": params}

    # Create test job
    job_id = JobQueue.create_job("test", {"test_param": "hello"})
    print(f"Created job: {job_id}")

    # Start worker
    start_job_worker()

    # Monitor job
    print("\nMonitoring job status...")
    for _ in range(10):
        time.sleep(1)
        status = JobQueue.get_job_status(job_id)
        if status:
            print(f"Status: {status['status']}, Progress: {status['progress']}%")
            if status['status'] in [JobStatus.COMPLETED, JobStatus.FAILED]:
                print(f"Final result: {status.get('result') or status.get('error')}")
                break

    # Stop worker
    stop_job_worker()
    print("\n✅ Test completed")
