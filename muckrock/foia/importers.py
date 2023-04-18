"""
How to import FOIA Logs from various formats
"""

# Standard Library
import io
import logging
from datetime import datetime

# Third Party
import openpyxl
import requests

# MuckRock
from muckrock.foia.models import FOIALog

logger = logging.getLogger(__name__)


def import_fda(url, agency):
    """Import a FOIA Log from the FDA"""
    logger.info("[FDA FOIA LOG] Importing FDA FOIA log from %s", url)
    resp = requests.get(url)
    logger.info("[FDA FOIA LOG] Response status code: %s", resp.status_code)
    resp.raise_for_status()
    file = io.BytesIO(resp.content)
    workbook = openpyxl.load_workbook(file)
    worksheet = workbook.active

    logs = []
    for row in worksheet.iter_rows(values_only=True, min_row=2):
        recd_date = datetime.strptime(row[1], "%m/%d/%Y").date()
        logs.append(
            FOIALog(
                request_id=row[0],
                requestor=row[2],
                date=recd_date,
                subject=row[4],
                agency=agency,
            )
        )

    logger.info("[FDA FOIA LOG] Logs found: %d", len(logs))
    FOIALog.objects.bulk_create(logs)
    logger.info("[FDA FOIA LOG] Logs created")
