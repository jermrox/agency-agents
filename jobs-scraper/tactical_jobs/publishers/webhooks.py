"""Network publishers: Discord and a generic JSON webhook."""

from __future__ import annotations

import time
from typing import Sequence

from ..http import FetchError, post_json
from ..models import JobPosting
from .base import Publisher

DISCORD_EMBED_LIMIT = 10
"""Discord accepts at most 10 embeds per message."""

DISCORD_DESCRIPTION_LIMIT = 300


class DiscordPublisher(Publisher):
    """Post new roles to a Discord channel via an incoming webhook.

    MOPs & MOEs already runs job traffic through Discord, so this is the
    lowest-friction destination -- it needs no site changes at all. Create the
    webhook in Server Settings -> Integrations -> Webhooks and pass the URL in
    via an environment variable.
    """

    kind = "discord"

    def publish(self, postings: Sequence[JobPosting]) -> str:
        if not postings:
            return "discord: nothing to post"
        url = self.require("webhook_url")
        username = self.options.get("username", "MOPs & MOEs Job Bot")
        delay = float(self.options.get("delay_seconds", 1.0))

        sent = 0
        for start in range(0, len(postings), DISCORD_EMBED_LIMIT):
            batch = postings[start : start + DISCORD_EMBED_LIMIT]
            embeds = []
            for posting in batch:
                fields = [
                    {
                        "name": "Location",
                        "value": (posting.location or "Not listed")
                        + (" · Remote" if posting.remote else ""),
                        "inline": True,
                    }
                ]
                if posting.compensation:
                    fields.append(
                        {"name": "Compensation", "value": posting.compensation, "inline": True}
                    )
                if posting.tags:
                    fields.append(
                        {"name": "Tags", "value": ", ".join(posting.tags), "inline": False}
                    )
                description = " ".join(posting.description.split())[
                    :DISCORD_DESCRIPTION_LIMIT
                ]
                embeds.append(
                    {
                        "title": f"{posting.title} — {posting.employer}"[:256],
                        "url": posting.url,
                        "description": description,
                        "fields": fields,
                        "footer": {"text": f"via {posting.source}"},
                    }
                )
            try:
                post_json(url, {"username": username, "embeds": embeds})
                sent += len(batch)
            except FetchError as exc:
                return f"discord: sent {sent}/{len(postings)} then failed: {exc}"
            # Stay well clear of Discord's webhook rate limit.
            if start + DISCORD_EMBED_LIMIT < len(postings):
                time.sleep(delay)
        return f"discord: posted {sent} job(s)"


class WebhookPublisher(Publisher):
    """POST the batch as JSON to an arbitrary endpoint.

    Use this to drive a Zapier/Make scenario, a Cloudflare Worker that writes
    to KV, or any custom CMS that *does* accept writes.
    """

    kind = "webhook"

    def publish(self, postings: Sequence[JobPosting]) -> str:
        if not postings:
            return "webhook: nothing to post"
        url = self.require("url")
        headers = dict(self.options.get("headers", {}))
        batch_size = int(self.options.get("batch_size", 25))

        sent = 0
        for start in range(0, len(postings), batch_size):
            batch = postings[start : start + batch_size]
            payload = {"jobs": [p.to_public_dict() for p in batch]}
            try:
                post_json(url, payload, headers=headers)
                sent += len(batch)
            except FetchError as exc:
                return f"webhook: sent {sent}/{len(postings)} then failed: {exc}"
        return f"webhook: posted {sent} job(s) to {url}"


WEBHOOK_PUBLISHERS: tuple[type[Publisher], ...] = (DiscordPublisher, WebhookPublisher)
