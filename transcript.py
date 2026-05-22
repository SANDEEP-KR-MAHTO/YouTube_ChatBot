import re
from youtube_transcript_api import YouTubeTranscriptApi


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
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id)
        full_text = " ".join(snippet.text for snippet in transcript_list)
        return full_text, video_id
    except Exception as e:
        raise RuntimeError(f"Could not fetch transcript: {e}")
