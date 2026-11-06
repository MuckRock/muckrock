"""
Utilities for handling incoming mail
"""

# Django
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction

# Standard Library
import logging
import re
import time

# Third Party
import requests
from botocore.exceptions import BotoCoreError, ClientError
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.core.utils import parse_header
from muckrock.foia.models.file import get_path

logger = logging.getLogger(__name__)


class DropboxDownloader:
    """Download configuration for dropbox links"""

    name = "DropBox"
    p_link = re.compile(r"https://www.dropbox.com/[a-zA-Z0-9$_.+!*\'(),;/?:@=&-]+")

    @staticmethod
    def preprocess(link):
        """Replace the overview page with a direct download of the zip"""
        return link.replace("dl=0", "dl=1")


class DownloadSkipped(Exception):
    """Raised when a download exceeds the size cap or the deadline"""


def stream_to_s3(response, path, start, deadline):
    """Stream a response body to S3, aborting the upload if over the cap or deadline"""
    full_path = f"s3://{settings.AWS_MEDIA_BUCKET_NAME}/{path}"
    total = 0
    with smart_open(full_path, "wb", s3_upload={"ACL": "public-read"}) as file_:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            total += len(chunk)
            if total > settings.MAX_LINK_DOWNLOAD_SIZE:
                raise DownloadSkipped(
                    f"exceeded {settings.MAX_LINK_DOWNLOAD_SIZE} bytes"
                )
            if time.monotonic() - start > deadline:
                raise DownloadSkipped(f"exceeded {deadline}s")
            file_.write(chunk)


def download_link(communication, link, start, deadline):
    """Stream one link to S3 and return its filename and S3 path"""
    with requests.get(link, timeout=10, stream=True) as response:
        response.raise_for_status()
        length = response.headers.get("Content-Length", "")
        if length.isdigit() and int(length) > settings.MAX_LINK_DOWNLOAD_SIZE:
            raise DownloadSkipped(f"Content-Length {length} over cap")
        _, params = parse_header(response.headers.get("content-disposition", ""))
        name = params.get("filename", "Untitled")
        path = get_path(name)
        logger.info("[DL:%s] Saving file %s", communication.pk, name)
        stream_to_s3(response, path, start, deadline)
    return name, path


def delete_downloaded(communication, downloaded):
    """Remove files already uploaded to S3 when the batch is abandoned"""
    for _, path in downloaded:
        try:
            default_storage.delete(path)
        except (BotoCoreError, ClientError) as exc:
            logger.error("[DL:%s] Could not delete %s: %s", communication.pk, path, exc)


def download_links(communication):
    """Download all links in the communication, attaching them only if all succeed"""
    # One deadline for the whole batch, half the task time limit
    deadline = int(settings.CELERY_TASK_TIME_LIMIT) / 2
    start = time.monotonic()
    downloaders = [DropboxDownloader]
    downloaded = []
    current = None
    logger.info("Trying to download links for communication %s", communication.pk)

    try:
        for downloader in downloaders:
            for found in downloader.p_link.findall(communication.communication):
                current = downloader.preprocess(found)
                logger.info("[DL:%s] Trying to download %s", communication.pk, current)
                downloaded.append(
                    download_link(communication, current, start, deadline)
                )
    except (DownloadSkipped, requests.exceptions.RequestException) as exc:
        logger.warning(
            "[DL:%s] Attaching nothing, %s failed: %s", communication.pk, current, exc
        )
        delete_downloaded(communication, downloaded)
        return
    except (BotoCoreError, ClientError) as exc:
        logger.error(
            "[DL:%s] Attaching nothing, storage error on %s: %s",
            communication.pk,
            current,
            exc,
        )
        delete_downloaded(communication, downloaded)
        return

    with transaction.atomic():
        for name, path in downloaded:
            communication.attach_file(path=path, name=name)
