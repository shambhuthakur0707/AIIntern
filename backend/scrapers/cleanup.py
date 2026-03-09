"""
cleanup.py — Automated Internship Database Cleanup

Removes:
  1. Fake / low-quality internships (spam signals, missing fields, gibberish)
  2. Expired internships (deadline passed or scraped too long ago)
  3. Dead internships (apply_url returns 404 / unreachable)

Designed to run as a periodic job alongside the scraper scheduler.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List

import requests

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────
# Internships older than this (from scraped_at / created_at) are expired
MAX_AGE_DAYS = 30

# HTTP timeout when checking apply_url liveness
LINK_CHECK_TIMEOUT = 8

# Max internships to link-check per run (to avoid hammering external sites)
LINK_CHECK_BATCH = 50

# ── Fake / spam detection signals ─────────────────────────────────────
_SPAM_TITLE_PATTERNS = [
    re.compile(r"(?:earn|make)\s+\$?\d+", re.IGNORECASE),
    re.compile(r"work\s+from\s+home.*\$", re.IGNORECASE),
    re.compile(r"(click\s+here|apply\s+now\s+free)", re.IGNORECASE),
    re.compile(r"(urgent|hurry|limited\s+time)", re.IGNORECASE),
    re.compile(r"(crypto|forex|trading)\s+(intern|job)", re.IGNORECASE),
    re.compile(r"(mlm|pyramid|network\s+marketing)", re.IGNORECASE),
]

# Minimum field quality thresholds
MIN_TITLE_LENGTH = 5
MIN_DESCRIPTION_LENGTH = 30


def _is_fake(doc: dict) -> str:
    """
    Return a reason string if the internship looks fake/spam,
    or empty string if it looks legitimate.
    """
    title = (doc.get("title") or "").strip()
    description = (doc.get("description") or "").strip()
    company = (doc.get("company") or "").strip()

    # Missing critical fields
    if not title or len(title) < MIN_TITLE_LENGTH:
        return "title missing or too short"
    if not company:
        return "company missing"
    if not description or len(description) < MIN_DESCRIPTION_LENGTH:
        return "description missing or too short"

    # Spam patterns in title
    for pattern in _SPAM_TITLE_PATTERNS:
        if pattern.search(title):
            return f"spam pattern in title: {pattern.pattern}"

    # No required_skills at all (likely a garbage entry)
    skills = doc.get("required_skills", [])
    if not skills or not any(s.strip() for s in skills):
        return "no required_skills"

    return ""


def _is_expired(doc: dict) -> bool:
    """Return True if the internship has exceeded MAX_AGE_DAYS."""
    # Check explicit deadline field first
    deadline = doc.get("deadline") or doc.get("application_deadline")
    if deadline:
        if isinstance(deadline, str):
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    deadline = datetime.strptime(deadline, fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue
        if isinstance(deadline, datetime):
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if deadline < datetime.now(timezone.utc):
                return True

    # Fall back to scraped_at / created_at age
    ref_date = doc.get("scraped_at") or doc.get("created_at")
    if ref_date:
        if isinstance(ref_date, datetime):
            if ref_date.tzinfo is None:
                ref_date = ref_date.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
            if ref_date < cutoff:
                return True

    return False


def _is_dead_link(url: str) -> bool:
    """Return True if the apply URL is unreachable or returns a clear error."""
    if not url or not url.startswith("http"):
        return False  # Can't check non-HTTP URLs; don't delete

    try:
        resp = requests.head(url, timeout=LINK_CHECK_TIMEOUT, allow_redirects=True)
        # 404, 410 Gone, or 403 (many sites block HEAD)
        if resp.status_code in (404, 410):
            return True
        # If HEAD is blocked, try GET
        if resp.status_code == 403:
            resp = requests.get(url, timeout=LINK_CHECK_TIMEOUT, allow_redirects=True, stream=True)
            resp.close()
            return resp.status_code in (404, 410)
        return False
    except requests.RequestException:
        # Network error — could be temporary, don't delete on first failure
        return False


def run_cleanup(db) -> dict:
    """
    Scan all internships and remove fake, expired, and dead-link entries.

    Args:
        db: MongoDB database instance.

    Returns:
        Summary dict with counts of removed internships per category.
    """
    stats = {"fake": 0, "expired": 0, "dead_link": 0, "total_checked": 0}
    ids_to_delete: List[dict] = []  # (id, reason) pairs

    all_docs = list(db.internships.find())
    stats["total_checked"] = len(all_docs)
    logger.info("Cleanup: scanning %d internships", len(all_docs))

    link_check_count = 0

    for doc in all_docs:
        doc_id = doc["_id"]

        # 1. Fake / spam check
        fake_reason = _is_fake(doc)
        if fake_reason:
            ids_to_delete.append({"_id": doc_id, "reason": f"fake: {fake_reason}"})
            stats["fake"] += 1
            continue

        # 2. Expired check
        if _is_expired(doc):
            ids_to_delete.append({"_id": doc_id, "reason": "expired"})
            stats["expired"] += 1
            continue

        # 3. Dead link check (batched)
        if link_check_count < LINK_CHECK_BATCH:
            apply_url = (doc.get("apply_url") or "").strip()
            if apply_url and apply_url.startswith("http"):
                link_check_count += 1
                if _is_dead_link(apply_url):
                    ids_to_delete.append({"_id": doc_id, "reason": "dead_link"})
                    stats["dead_link"] += 1
                    continue

    # Bulk delete
    if ids_to_delete:
        delete_ids = [item["_id"] for item in ids_to_delete]
        result = db.internships.delete_many({"_id": {"$in": delete_ids}})
        logger.info(
            "Cleanup: removed %d internships (fake=%d, expired=%d, dead_link=%d)",
            result.deleted_count, stats["fake"], stats["expired"], stats["dead_link"],
        )

        # Also clean up cached analyses for deleted internships
        str_ids = [str(i) for i in delete_ids]
        db.internship_analyses.delete_many(
            {"cache_key": {"$regex": "|".join(str_ids)}}
        )
    else:
        logger.info("Cleanup: no internships to remove.")

    return stats
