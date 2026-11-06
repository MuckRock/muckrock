"""
Utilities for handling incoming mail
"""

# Django
from django.conf import settings

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
from muckrock.task.models import FlaggedTask

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


def note_failed_download(communication, link, reason):
    """Note a failed link on the request's open download-file flag"""
    task = (
        FlaggedTask.objects.filter(
            foia=communication.foia,
            category="download file",
            resolved=False,
            text__contains=link,
        )
        .order_by("-date_created")
        .first()
    )
    if task is None:
        logger.error(
            "[DL:%s] Download of %s failed and no open flag to note it on (%s)",
            communication.pk,
            link,
            reason,
        )
        return
    task.note += f"Automatic download failed for {link} ({reason})\n"
    task.save(update_fields=["note"])


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


def download_links(communication):
    """Download links from the communication, streaming each straight to S3"""
    # Half the task time limit, leaving room for other links
    deadline = int(settings.CELERY_TASK_TIME_LIMIT) / 2
    downloaders = [DropboxDownloader]
    logger.info("Trying to download links for communication %s", communication.pk)

    for downloader in downloaders:
        logger.info("[DL:%s] Looking for %s links", communication.pk, downloader.name)
        for found in downloader.p_link.findall(communication.communication):
            link = downloader.preprocess(found)
            logger.info("[DL:%s] Trying to download %s", communication.pk, link)
            start = time.monotonic()
            try:
                with requests.get(link, timeout=10, stream=True) as response:
                    response.raise_for_status()
                    length = response.headers.get("Content-Length", "")
                    if (
                        length.isdigit()
                        and int(length) > settings.MAX_LINK_DOWNLOAD_SIZE
                    ):
                        logger.warning(
                            "[DL:%s] Skipping %s, Content-Length %s over cap",
                            communication.pk,
                            link,
                            length,
                        )
                        note_failed_download(
                            communication, found, f"Content-Length {length} over cap"
                        )
                        continue
                    _, params = parse_header(
                        response.headers.get("content-disposition", "")
                    )
                    name = params.get("filename", "Untitled")
                    path = get_path(name)
                    logger.info("[DL:%s] Saving file %s", communication.pk, name)
                    stream_to_s3(response, path, start, deadline)
                communication.attach_file(path=path, name=name)
            except DownloadSkipped as exc:
                logger.warning("[DL:%s] Skipping %s, %s", communication.pk, link, exc)
                note_failed_download(communication, found, exc)
            except requests.exceptions.RequestException as exc:
                logger.info("[DL:%s] Error %s", communication.pk, exc)
                note_failed_download(communication, found, exc)
            except (BotoCoreError, ClientError) as exc:
                logger.error(
                    "[DL:%s] Storage error saving %s: %s", communication.pk, link, exc
                )
                note_failed_download(communication, found, f"storage error: {exc}")
