"""
Utilities for handling incoming mail
"""

# Standard Library
import cgi
import logging
import re

# Third Party
import requests

logger = logging.getLogger(__name__)


class DropboxDownloader:
    """Download configuration for dropbox links"""

    name = "DropBox"
    p_link = re.compile(r"https://www.dropbox.com/[a-zA-Z0-9$_.+!*\'(),;/?:@=&-]+")

    @staticmethod
    def preprocess(link):
        """Replace the overview page with a direct download of the zip"""
        return link.replace("dl=0", "dl=1")


def download_links(communication):
    """Download links from the communication"""
    downloaders = [DropboxDownloader]
    logger.info("Trying to download links for communication %s", communication.pk)

    for downloader in downloaders:
        logger.info("[DL:%s] Looking for %s links", communication.pk, downloader.name)
        for link in downloader.p_link.findall(communication.communication):
            link = downloader.preprocess(link)
            logger.info("[DL:%s] Trying to download %s", communication.pk, link)
            try:
                response = requests.get(link)
                response.raise_for_status()
            except requests.exceptions.RequestException as exc:
                logger.info("[DL:%s] Error %s", communication.pk, exc)
            _, params = cgi.parse_header(
                response.headers.get("content-disposition", "")
            )
            name = params.get("filename", "Untitled")
            logger.info("[DL:%s] Saving file %s", communication.pk, name)
            content = response.content
            communication.attach_file(content=content, name=name)
