import os
import re
from youtube_transcript_api import YouTubeTranscriptApi


def _build_api() -> YouTubeTranscriptApi:
    """
    Return a YouTubeTranscriptApi instance, optionally with proxy support.

    Checks in priority order:
    1. ScraperAPI    (SCRAPER_API_KEY)                              — 1,000 free req/month
    2. Webshare      (WEBSHARE_PROXY_USERNAME + _PASSWORD)          — paid residential
    3. Generic proxy (HTTP_PROXY or HTTPS_PROXY env var)            — any other provider
    4. No proxy                                                     — local dev only
    """
    # 1. ScraperAPI — residential IPs, free tier sufficient for personal projects
    scraper_key = os.getenv("SCRAPER_API_KEY")
    if scraper_key:
        from youtube_transcript_api.proxies import GenericProxyConfig
        proxy_url = f"http://scraperapi:{scraper_key}@proxy-server.scraperapi.com:8001"
        return YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(
                http_url=proxy_url,
                https_url=proxy_url,
            )
        )

    # 2. Webshare residential proxies (paid plan required for residential IPs)
    webshare_user = os.getenv("WEBSHARE_PROXY_USERNAME")
    webshare_pass = os.getenv("WEBSHARE_PROXY_PASSWORD")
    if webshare_user and webshare_pass:
        from youtube_transcript_api.proxies import WebshareProxyConfig
        return YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=webshare_user,
                proxy_password=webshare_pass,
            )
        )

    # 3. Generic HTTP/HTTPS proxy
    proxy_url = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    if proxy_url:
        from youtube_transcript_api.proxies import GenericProxyConfig
        return YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(
                http_url=proxy_url,
                https_url=proxy_url,
            )
        )

    # 4. No proxy — works locally, blocked on cloud provider IPs
    return YouTubeTranscriptApi()


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_transcript(url: str) -> tuple[str, str]:
    """Returns (transcript_text, video_id)."""
    video_id = extract_video_id(url)

    try:
        api = _build_api()
        transcript_list = api.fetch(video_id)
        full_text = " ".join(snippet.text for snippet in transcript_list)
        return full_text, video_id
    except Exception as e:
        raise RuntimeError(f"Could not fetch transcript: {e}")
