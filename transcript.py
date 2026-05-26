import os
import re
import json
import html
import requests
import xml.etree.ElementTree as ET
from youtube_transcript_api import YouTubeTranscriptApi


# ---------------------------------------------------------------------------
# ScraperAPI-based fetcher  (Streamlit Cloud / any cloud deployment)
#
# Uses ScraperAPI's *API mode*:  GET https://api.scraperapi.com/?api_key=...&url=...
# ScraperAPI fetches YouTube from a residential IP and returns the HTML/XML to us.
# This is a plain HTTPS call to api.scraperapi.com — no proxy tunnelling,
# no SSL interception, no certificate errors.
# ---------------------------------------------------------------------------

def _scraper_get(url: str, api_key: str, timeout: int = 30) -> str:
    """Fetch a URL through ScraperAPI's API endpoint and return the response text."""
    resp = requests.get(
        "https://api.scraperapi.com/",
        params={"api_key": api_key, "url": url},
        timeout=timeout,
    )
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

    # Prefer English captions; fall back to first available language
    for track in tracks:
        if track.get("languageCode", "").startswith("en"):
            return track["baseUrl"]

    return tracks[0]["baseUrl"]


def _parse_timed_text(xml_text: str) -> str:
    """Convert YouTube's timed-text XML into a plain-text string."""
    root = ET.fromstring(xml_text)
    parts = []
    for elem in root.iter("text"):
        raw = elem.text or ""
        clean = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
        if clean:
            parts.append(clean)
    return " ".join(parts)


def _fetch_via_scraperapi(video_id: str, api_key: str) -> str:
    """Full transcript fetch using ScraperAPI API mode (no proxy, no SSL issues)."""
    page_html = _scraper_get(
        f"https://www.youtube.com/watch?v={video_id}", api_key
    )
    caption_url = _extract_caption_url(page_html)
    caption_xml = _scraper_get(caption_url, api_key)
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

    - SCRAPER_API_KEY set  →  ScraperAPI API mode  (cloud-safe, no IP/SSL issues)
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
