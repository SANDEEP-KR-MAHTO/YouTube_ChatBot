import os
import re
import json
import html
import requests
import xml.etree.ElementTree as ET
from youtube_transcript_api import YouTubeTranscriptApi


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _scraper_get(url: str, api_key: str, timeout: int = 30) -> str:
    """Fetch a URL through ScraperAPI's API endpoint (residential IP)."""
    resp = requests.get(
        "https://api.scraperapi.com/",
        params={"api_key": api_key, "url": url},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.text


def _direct_get(url: str, timeout: int = 30) -> str:
    """Fetch a URL directly with a browser-like User-Agent."""
    resp = requests.get(url, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _extract_caption_url(page_html: str) -> str:
    """
    Parse ytInitialPlayerResponse from a YouTube watch page and return
    the URL of the first available English caption track.
    """
    marker = re.search(r"ytInitialPlayerResponse\s*=\s*", page_html)
    if not marker:
        raise RuntimeError(
            "Could not find player data in the YouTube page. "
            "The video may be private, age-restricted, or unavailable."
        )

    try:
        player, _ = json.JSONDecoder().raw_decode(page_html, marker.end())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse YouTube player data: {exc}")

    tracks = (
        player
        .get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )

    if not tracks:
        raise RuntimeError(
            "No captions found for this video. "
            "Make sure the video has subtitles or auto-generated captions enabled."
        )

    for track in tracks:
        if track.get("languageCode", "").startswith("en"):
            return track["baseUrl"]

    return tracks[0]["baseUrl"]


def _parse_timed_text(xml_text: str) -> str:
    """Convert YouTube's timed-text XML into a plain-text string."""
    xml_text = xml_text.strip()
    if not xml_text:
        raise RuntimeError(
            "YouTube returned empty caption data. "
            "The video may not have captions available."
        )
    root = ET.fromstring(xml_text)
    parts = []
    for elem in root.iter("text"):
        raw = elem.text or ""
        clean = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
        if clean:
            parts.append(clean)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Transcript fetchers
# ---------------------------------------------------------------------------

def _fetch_via_scraperapi(video_id: str, api_key: str) -> str:
    """
    Hybrid approach:
      Step 1 — Watch page  : fetched via ScraperAPI (residential IP, bypasses block)
      Step 2 — Caption XML : fetched directly       (signed URL works from any IP)

    The YouTube timedtext URL contains ip=0.0.0.0 in its signed params, meaning
    it is not tied to a specific IP and can be fetched from any server.
    Using ScraperAPI for this step returns empty content — hence the direct fetch.
    """
    # Step 1: get the watch page through a residential IP
    page_html = _scraper_get(
        f"https://www.youtube.com/watch?v={video_id}", api_key
    )

    if len(page_html) < 1000:
        raise RuntimeError(
            "ScraperAPI returned an unexpectedly short page — "
            "the video may be unavailable or your ScraperAPI quota may be exhausted."
        )

    # Step 2: extract the signed caption URL
    caption_url = _extract_caption_url(page_html)

    # Step 3: fetch the caption XML directly (no proxy needed)
    caption_xml = _direct_get(caption_url)
    return _parse_timed_text(caption_xml)


# ---------------------------------------------------------------------------
# Video ID extraction
# ---------------------------------------------------------------------------

def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_transcript(url: str) -> tuple[str, str]:
    """
    Returns (transcript_text, video_id).

    - SCRAPER_API_KEY set  →  hybrid ScraperAPI fetch  (Streamlit Cloud safe)
    - No key              →  direct youtube-transcript-api  (local dev only)
    """
    video_id = extract_video_id(url)
    scraper_key = os.getenv("SCRAPER_API_KEY")

    try:
        if scraper_key:
            transcript = _fetch_via_scraperapi(video_id, scraper_key)
        else:
            api = YouTubeTranscriptApi()
            transcript_list = api.fetch(video_id)
            transcript = " ".join(snippet.text for snippet in transcript_list)

        return transcript, video_id
    except Exception as exc:
        raise RuntimeError(f"Could not fetch transcript: {exc}")
