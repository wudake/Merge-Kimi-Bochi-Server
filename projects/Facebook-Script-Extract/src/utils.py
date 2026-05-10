import re
from urllib.parse import urlparse


FACEBOOK_URL_PATTERNS = [
    r"https?://(?:www\.)?facebook\.com/watch\?v=[\w-]+",
    r"https?://(?:www\.)?facebook\.com/share/v/[\w-]+/?",
    r"https?://(?:www\.)?facebook\.com/share/r/[\w-]+/?",
    r"https?://fb\.watch/[\w-]+",
    r"https?://(?:www\.)?facebook\.com/[^/]+/videos/[\w-]+",
    r"https?://(?:www\.)?facebook\.com/groups/[^/]+/posts/[\w-]+",
    r"https?://(?:www\.)?facebook\.com/ads/library/\?id=[\d]+",
]

YOUTUBE_URL_PATTERNS = [
    r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",
    r"https?://(?:www\.)?youtube\.com/shorts/[\w-]+",
    r"https?://youtu\.be/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/embed/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/v/[\w-]+",
]

VIDEO_URL_PATTERNS = FACEBOOK_URL_PATTERNS + YOUTUBE_URL_PATTERNS


def is_valid_video_url(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    for pattern in VIDEO_URL_PATTERNS:
        if re.match(pattern, url):
            return True
    return False


def is_valid_facebook_url(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    for pattern in FACEBOOK_URL_PATTERNS:
        if re.match(pattern, url):
            return True
    return False


def extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)

    # YouTube URLs
    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        if "watch" in parsed.path and "v=" in parsed.query:
            match = re.search(r"v=([\w-]+)", parsed.query)
            if match:
                return match.group(1)
        match = re.search(r"/shorts/([\w-]+)", url)
        if match:
            return match.group(1)
        match = re.search(r"youtu\.be/([\w-]+)", url)
        if match:
            return match.group(1)
        match = re.search(r"/embed/([\w-]+)", url)
        if match:
            return match.group(1)
        match = re.search(r"/v/([\w-]+)", url)
        if match:
            return match.group(1)
        return None

    # Facebook URLs
    if "watch" in parsed.path and "v=" in parsed.query:
        match = re.search(r"v=([\w-]+)", parsed.query)
        if match:
            return match.group(1)
    match = re.search(r"/videos/(\w+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/share/v/(\w+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/share/r/(\w+)", url)
    if match:
        return match.group(1)
    match = re.search(r"fb\.watch/(\w+)", url)
    if match:
        return match.group(1)
    return None
