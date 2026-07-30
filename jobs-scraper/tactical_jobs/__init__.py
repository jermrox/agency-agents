"""Tactical human performance job aggregator for MOPs & MOEs.

Pulls open roles from employer ATS boards and USAJOBS, scores them for
relevance to tactical human performance, drops duplicates, and publishes the
survivors to a feed, Discord, or a review queue.
"""

from .models import JobPosting, SourceError

__version__ = "0.1.0"
__all__ = ["JobPosting", "SourceError", "__version__"]
