"""Normalization and type-checking helpers for scraped Instagram post records."""

from __future__ import annotations

from typing import Any

DEFAULT_PROFILE_URLS: list[str] = [
    'https://www.instagram.com/remaxconexionpy_/',
    'https://www.instagram.com/rblack.py/',
    'https://www.instagram.com/remaxelitepy/',
    'https://www.instagram.com/remaxrealtypy/',
    'https://www.instagram.com/remaxselection/',
]

MAX_POSTS_PER_PROFILE_CAP = 250


def _as_str(val: Any) -> str | None:
    if val is None:
        return None
    return str(val)


def _as_int(val: Any) -> int | None:
    if val is None or isinstance(val, bool):
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _as_float(val: Any) -> float | None:
    if val is None or isinstance(val, bool):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _as_bool(val: Any) -> bool | None:
    if isinstance(val, bool):
        return val
    return None


def _as_list_of_str(val: Any) -> list[str]:
    if not isinstance(val, list):
        return []
    return [str(item) for item in val if item is not None]


def _as_list_of_dicts(val: Any) -> list[dict[str, Any]]:
    if not isinstance(val, list):
        return []
    return [item for item in val if isinstance(item, dict)]


def _as_tagged_users(val: Any) -> list[dict[str, Any] | str]:
    if not isinstance(val, list):
        return []
    return [item for item in val if isinstance(item, (dict, str))]


def normalize_post_item(raw: dict[str, Any], fallback_input_url: str | None = None) -> dict[str, Any]:
    """Validate and normalize a raw post item from apify/instagram-scraper to match dataset_schema.json."""
    short_code = _as_str(raw.get('shortCode'))
    url = _as_str(raw.get('url')) or (f'https://www.instagram.com/p/{short_code}/' if short_code else '')

    music_info = raw.get('musicInfo')
    if not isinstance(music_info, dict):
        music_info = None

    return {
        # 1. Identificadores y enlaces
        'id': _as_str(raw.get('id')),
        'shortCode': short_code or '',
        'url': url,
        'inputUrl': _as_str(raw.get('inputUrl')) or fallback_input_url,
        'timestamp': _as_str(raw.get('timestamp')),
        # 2. Contenido y formato (Video / Image / Sidecar)
        'type': _as_str(raw.get('type')),
        'productType': _as_str(raw.get('productType')),
        'caption': _as_str(raw.get('caption')),
        'alt': _as_str(raw.get('alt')),
        'displayUrl': _as_str(raw.get('displayUrl')),
        'videoUrl': _as_str(raw.get('videoUrl')),
        'videoDuration': _as_float(raw.get('videoDuration')),
        'images': _as_list_of_str(raw.get('images')),
        'childPosts': _as_list_of_dicts(raw.get('childPosts')),
        # 3. Métricas públicas
        'likesCount': _as_int(raw.get('likesCount')),
        'commentsCount': _as_int(raw.get('commentsCount')),
        'videoViewCount': _as_int(raw.get('videoViewCount')),
        'videoPlayCount': _as_int(raw.get('videoPlayCount')),
        # 4. Metadatos y autoría
        'ownerUsername': _as_str(raw.get('ownerUsername')),
        'ownerFullName': _as_str(raw.get('ownerFullName')),
        'ownerId': _as_str(raw.get('ownerId')),
        'coauthorProducers': _as_list_of_dicts(raw.get('coauthorProducers')),
        'taggedUsers': _as_tagged_users(raw.get('taggedUsers')),
        # 5. Taxonomía y SEO
        'hashtags': _as_list_of_str(raw.get('hashtags')),
        'mentions': _as_list_of_str(raw.get('mentions')),
        'locationName': _as_str(raw.get('locationName')),
        'locationId': _as_str(raw.get('locationId')),
        # 6. Música / Audio
        'musicInfo': music_info,
        # 7. Comentarios
        'firstComment': _as_str(raw.get('firstComment')),
        'latestComments': _as_list_of_dicts(raw.get('latestComments')),
        # Flags adicionales
        'isPinned': _as_bool(raw.get('isPinned')),
        'isSponsored': _as_bool(raw.get('isSponsored')),
    }
