import os
import re
from youtube_transcript_api import YouTubeTranscriptApi


def _build_api() -> YouTubeTranscriptApi:
    """
    Return a YouTubeTranscriptApi instance, optionally with proxy support.

    Priority order:
    1. Webshare rotating proxies  (WEBSHARE_PROXY_USERNAME + WEBSHARE_PROXY_PASSWORD)
       → Best for Streamlit Cloud; sign up free at https://proxy.webshare.io
    2. Generic HTTP/HTTPS proxy   (HTTP_PROXY or HTTPS_PROXY env var)
       → Any other proxy provider
    3. No proxy — works locally, blocked on most cloud provider IPs
    """
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

    proxy_url = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    if proxy_url:
        from youtube_transcript_api.proxies import GenericProxyConfig
        return YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(
                http_url=proxy_url,
                https_url=proxy_url,
            )
        )

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
