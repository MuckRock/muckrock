"""
Utilities for handling incoming mail
"""

# Django
from django.conf import settings
from django.core.files import File

# Standard Library
import logging
import re
import tempfile
import time

# Third Party
import requests

# MuckRock
from muckrock.core.utils import parse_header

logger = logging.getLogger(__name__)


class DropboxDownloader:
    """Download configuration for dropbox links"""

    name = "DropBox"
    p_link = re.compile(r"https://www.dropbox.com/[a-zA-Z0-9$_.+!*\'(),;/?:@=&-]+")

    @staticmethod
    def preprocess(link):
        """Replace the overview page with a direct download of the zip"""
        return link.replace("dl=0", "dl=1")


def fetch_link(communication, link, file_):
    """Stream a link into file_ with a size cap and total deadline
    return the filename or None."""
    # Half the task time limit, leaving room to attach_file and run other links
    deadline = int(settings.CELERY_TASK_TIME_LIMIT) / 2
    start = time.monotonic()
    try:
        with requests.get(link, timeout=10, stream=True) as response:
            response.raise_for_status()
            length = response.headers.get("Content-Length", "")
            if length.isdigit() and int(length) > settings.MAX_LINK_DOWNLOAD_SIZE:
                logger.warning(
                    "[DL:%s] Skipping %s, Content-Length %s over cap",
                    communication.pk,
                    link,
                    length,
                )
                return None
            _, params = parse_header(response.headers.get("content-disposition", ""))
            name = params.get("filename", "Untitled")
            total = 0
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                total += len(chunk)
                if total > settings.MAX_LINK_DOWNLOAD_SIZE:
                    logger.warning(
                        "[DL:%s] Skipping %s, exceeded %s bytes",
                        communication.pk,
                        link,
                        settings.MAX_LINK_DOWNLOAD_SIZE,
                    )
                    return None
                if time.monotonic() - start > deadline:
                    logger.warning(
                        "[DL:%s] Skipping %s, exceeded %ss",
                        communication.pk,
                        link,
                        deadline,
                    )
                    return None
                file_.write(chunk)
    except requests.exceptions.RequestException as exc:
        logger.info("[DL:%s] Error %s", communication.pk, exc)
        return None
    return name


def download_links(communication):
    """Download links from the communication"""
    downloaders = [DropboxDownloader]
    logger.info("Trying to download links for communication %s", communication.pk)

    for downloader in downloaders:
        logger.info("[DL:%s] Looking for %s links", communication.pk, downloader.name)
        for link in downloader.p_link.findall(communication.communication):
            link = downloader.preprocess(link)
            logger.info("[DL:%s] Trying to download %s", communication.pk, link)
            with tempfile.TemporaryFile() as tmp:
                name = fetch_link(communication, link, tmp)
                if name is None:
                    continue
                tmp.seek(0)
                logger.info("[DL:%s] Saving file %s", communication.pk, name)
                communication.attach_file(file_=File(tmp, name=name), name=name)
