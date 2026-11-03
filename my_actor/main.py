"""Main entry point for the Instagram Public Profile & Post Scraper Actor.

Orchestrates `apify/instagram-scraper` across target Instagram profile URLs,
strictly capping extraction at the last 250 posts per account and storing
normalized public metadata, metrics, carousels, audio, and comments.
"""

from __future__ import annotations

from typing import Any

from apify import Actor, Event

from .routes import (
    DEFAULT_PROFILE_URLS,
    MAX_POSTS_PER_PROFILE_CAP,
    normalize_post_item,
)


def _normalize_profile_urls(raw_urls: Any) -> list[str]:
    """Extract clean URL strings from input profile_urls list."""
    if not isinstance(raw_urls, list):
        return list(DEFAULT_PROFILE_URLS)
    cleaned: list[str] = []
    for entry in raw_urls:
        if isinstance(entry, str) and entry.strip():
            cleaned.append(entry.strip())
        elif isinstance(entry, dict) and isinstance(entry.get('url'), str) and entry['url'].strip():
            cleaned.append(entry['url'].strip())
    return cleaned


async def main() -> None:
    """Execute the Instagram post extraction workflow."""
    async with Actor:
        per_account_tally: dict[str, int] = {}
        total_pushed = 0
        aborted = False

        async def persist_summary(status: str) -> None:
            summary_payload = {
                'status': status,
                'maxPostsPerProfileCap': MAX_POSTS_PER_PROFILE_CAP,
                'totalPostsExtracted': total_pushed,
                'postsPerAccount': per_account_tally,
            }
            await Actor.set_value('SUMMARY', summary_payload)

        async def on_aborting() -> None:
            nonlocal aborted
            aborted = True
            Actor.log.warning('Actor is aborting! Persisting SUMMARY state before exiting...')
            await persist_summary(status='ABORTED')
            await Actor.exit()

        Actor.on(Event.ABORTING, on_aborting)

        actor_input = await Actor.get_input() or {}

        profile_urls = _normalize_profile_urls(
            actor_input.get('profile_urls', DEFAULT_PROFILE_URLS)
        )
        if not profile_urls:
            Actor.log.info('No Instagram profile URLs provided in input. Exiting.')
            await persist_summary(status='NO_INPUT_URLS')
            await Actor.exit()
            return

        raw_limit = actor_input.get('results_limit', MAX_POSTS_PER_PROFILE_CAP)
        try:
            requested_limit = int(raw_limit)
        except (ValueError, TypeError):
            requested_limit = MAX_POSTS_PER_PROFILE_CAP

        # Enforce hard cap: ONLY AND EXCLUSIVELY up to the last 250 posts per account
        results_limit = max(1, min(requested_limit, MAX_POSTS_PER_PROFILE_CAP))
        if requested_limit > MAX_POSTS_PER_PROFILE_CAP:
            Actor.log.warning(
                f'Requested results_limit ({requested_limit}) exceeds the strict 250-post cap. '
                f'Clamping to {MAX_POSTS_PER_PROFILE_CAP} posts per account.'
            )

        upstream_actor_id = str(actor_input.get('actor_id') or 'apify/instagram-scraper').strip()
        add_parent_data = bool(actor_input.get('add_parent_data', True))

        Actor.log.info(
            f'Starting Instagram extraction for {len(profile_urls)} profile(s) using {upstream_actor_id} '
            f'(strict limit: {results_limit} posts per account).'
        )

        upstream_run_input: dict[str, Any] = {
            'directUrls': profile_urls,
            'resultsType': 'posts',
            'resultsLimit': results_limit,
            'addParentData': add_parent_data,
        }

        actor_run = await Actor.call(
            actor_id=upstream_actor_id,
            run_input=upstream_run_input,
        )

        if actor_run is None or not actor_run.default_dataset_id:
            Actor.log.error(f'Upstream Actor {upstream_actor_id} did not return a valid run or dataset.')
            await persist_summary(status='UPSTREAM_FAILED')
            await Actor.exit(exit_code=1)
            return

        Actor.log.info(
            f'Upstream run finished (dataset ID: {actor_run.default_dataset_id}). '
            'Fetching, validating, and enforcing the 250-post per-account limit...'
        )

        dataset_client = Actor.apify_client.dataset(actor_run.default_dataset_id)
        batch: list[dict[str, Any]] = []

        async for raw_item in dataset_client.iterate_items():
            if aborted:
                break
            if not isinstance(raw_item, dict):
                continue

            # Skip error items returned when a profile has fewer posts or is unavailable
            if raw_item.get('error') and not raw_item.get('shortCode'):
                Actor.log.warning(f'Upstream warning/error item: {raw_item.get("error")} ({raw_item.get("url")})')
                continue

            normalized = normalize_post_item(raw_item)
            if not normalized['shortCode'] or not normalized['url']:
                continue

            account_key = (
                normalized.get('ownerUsername')
                or normalized.get('inputUrl')
                or 'unknown_account'
            )

            current_count = per_account_tally.get(account_key, 0)
            if current_count >= results_limit:
                # Strictly enforce <= 250 posts per account even if upstream returns extras
                continue

            per_account_tally[account_key] = current_count + 1
            total_pushed += 1
            batch.append(normalized)

            if len(batch) >= 100:
                await Actor.push_data(batch)
                batch.clear()

        if batch and not aborted:
            await Actor.push_data(batch)
            batch.clear()

        await persist_summary(status='COMPLETED')
        Actor.log.info(
            f'Completed Instagram scrape! Total posts saved: {total_pushed}. '
            f'Per-account breakdown: {per_account_tally}'
        )
