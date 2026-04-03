"""
Sprint 4 — Fraud Background Tasks
Celery tasks for offline ML scoring, Qdrant indexing, and generating risk reports.
"""
# TODO: Sprint 4 — implement this module

from app.worker import celery_app

@celery_app.task
def index_user_embeddings(user_id: str):
    """
    Background task to compute user behavioral embeddings and push to Qdrant.
    """
    raise NotImplementedError("Sprint 4: implement background vector indexing")
