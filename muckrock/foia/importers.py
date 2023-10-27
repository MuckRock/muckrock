"""
How to import FOIA Logs from various formats
"""

# Standard Library
import codecs
import csv
import logging
from datetime import date

# Third Party
from dateutil.parser import parse

# MuckRock
from muckrock.foia.models import FOIALog, FOIALogEntry
from muckrock.foia.models.request import STATUS, TrackingNumber

logger = logging.getLogger(__name__)


def parse_date(date_):
    """deal with missing dates"""
    if not date_:
        return None
    return parse(date_)


def import_logs(form, user):
    """Import a generic FOIA Log"""
    logger.info("[FOIA LOG IMPORT] Importing a FOIA log")

    foia_log = form.save(commit=False)
    foia_log.user = user
    foia_log.save()

    file = form.cleaned_data["log"]
    reader = csv.DictReader(codecs.iterdecode(file, "utf8"))
    logs = []
    statuses = set(s[0] for s in STATUS)
    tracking_ids = []
    for row in reader:
        tracking_ids.append(row["request id"])
    tracking_id_objs = TrackingNumber.objects.filter(
        tracking_id__in=tracking_ids, foia__agency=foia_log.agency
    )
    tracking_ids_map = {t.tracking_id: t.foia_id for t in tracking_id_objs}

    file.seek(0)
    reader = csv.DictReader(codecs.iterdecode(file, "utf8"))
    for row in reader:
        try:
            status = row.get("status", "")
            if status and status not in statuses:
                raise ValueError
            logs.append(
                FOIALogEntry(
                    request_id=row["request id"],
                    requester=row.get("requester", ""),
                    requester_organization=row.get("requester_organization", ""),
                    exemptions=row.get("exemptions", ""),
                    subject=row["subject"],
                    date_requested=parse_date(row.get("date requested")),
                    date_completed=parse_date(row.get("date completed")),
                    status=row.get("status", ""),
                    foia_request_id=tracking_ids_map.get(row["request id"]),
                    foia_log=foia_log,
                )
            )
        except (KeyError, ValueError) as exc:
            logger.warning(
                "[FOIA LOG IMPORT] Error importing %s - %s",
                row.get("request id", ""),
                exc,
            )

    foia_log.agency.last_log_update = date.today()
    foia_log.agency.save()
    logger.info("[FOIA LOG IMPORT] Logs found: %d", len(logs))
    objs = FOIALogEntry.objects.bulk_create(logs, ignore_conflicts=True)
    logger.info("[FOIA LOG IMPORT] Logs created: %d", len(objs))
    return len(objs)
