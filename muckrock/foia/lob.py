"""
Sending FOIA communications through Lob
"""

# Django
from django.conf import settings
from django.contrib.auth.models import User

# Standard Library
import json

# Third Party
from constance import config
from lob_python import ApiClient, Configuration
from lob_python.api.checks_api import ChecksApi
from lob_python.api.letters_api import LettersApi
from lob_python.model.address_domestic import AddressDomestic
from lob_python.model.address_editable import AddressEditable
from lob_python.model.check_editable import CheckEditable
from lob_python.model.chk_use_type import ChkUseType
from lob_python.model.letter_editable import LetterEditable
from lob_python.model.ltr_use_type import LtrUseType
from lob_python.model.metadata_model import MetadataModel

# MuckRock
from muckrock.communication.models import Check, MailCommunication
from muckrock.task.pdf import LobPDF

TIMEOUT = (10, 120)


def skip_reason(comm, address, amount, force):
    """Why this communication must be mailed by hand instead of through Lob, if so"""
    for test, reason in [
        (not config.AUTO_LOB and not force, "auto"),
        (not address, "addr"),
        (address and address.lob_errors(comm.foia.agency), "badadd"),
        (comm.category == "a" and not config.AUTO_LOB_APPEAL and not force, "appeal"),
        (comm.category == "p" and not config.AUTO_LOB_PAY and not force, "pay"),
        (amount > settings.CHECK_LIMIT and not force, "limit"),
    ]:
        if test:
            return reason
    return None


def prepare_mail(comm, address, switch, amount, num_msgs, *, retrying):
    """The MailCommunication to send through Lob, or the reason to mail it by hand

    Returns (mail, None) or (None, reason). A retry reuses the first attempt's
    PDF: Lob may already have that attempt, and a retry under the same
    idempotency key must send the same file.
    """
    if retrying:
        mail = MailCommunication.objects.filter(communication=comm).first()
        if mail and mail.pdf:
            return mail, None

    pdf = LobPDF(comm, comm.category, switch, amount=amount)
    prepared_pdf, total_page_count, _files, mail = pdf.prepare(address, num_msgs)
    if prepared_pdf is None:
        return None, "pdf"
    if total_page_count > 12:
        return None, "page"
    return mail, None


def error_message(exc):
    """Lob's error message from an ApiException, or the HTTP reason"""
    try:
        return json.loads(exc.body)["error"]["message"]
    except (TypeError, ValueError, KeyError):
        return str(exc.reason)


def _from_address(comm):
    """MuckRock's return address, as Lob's address fields"""
    return {
        "name": settings.ADDRESS_NAME,
        "company": settings.ADDRESS_DEPT.format(pk=comm.foia.pk),
        "address_line1": settings.ADDRESS_STREET,
        "address_city": settings.ADDRESS_CITY,
        "address_state": settings.ADDRESS_STATE,
        "address_zip": settings.ADDRESS_ZIP,
    }


def create_letter(comm, mail, certified, idempotency_key):
    """Send a letter via Lob"""
    letter = LetterEditable(
        description="Letter for communication {}".format(comm.pk),
        to=AddressEditable(**comm.foia.address.lob_format(comm.foia.agency)),
        _from=AddressEditable(**_from_address(comm)),
        file=mail.pdf.url,
        use_type=LtrUseType("operational"),
        color=False,
        double_sided=True,
        metadata=MetadataModel(mail_id=str(mail.pk)),
        extra_service=certified,
    )
    with ApiClient(Configuration(username=settings.LOB_SECRET_KEY)) as client:
        return LettersApi(client).create(
            letter, idempotency_key=idempotency_key, _request_timeout=TIMEOUT
        )


def create_check(comm, mail, check_address, amount, idempotency_key):
    """Send a check via Lob"""
    memo = "MR {}".format(comm.foia.pk)
    tracking_number = comm.foia.current_tracking_id()
    if tracking_number:
        old_memo = memo
        memo += " / {}".format(tracking_number)
        if len(memo) > 40:
            memo = old_memo

    check_editable = CheckEditable(
        description="Check for communication {}".format(comm.pk),
        to=AddressDomestic(**check_address.lob_format(comm.foia.agency)),
        _from=AddressDomestic(**_from_address(comm)),
        bank_account=settings.LOB_BANK_ACCOUNT_ID,
        amount=amount,
        memo=memo,
        attachment=mail.pdf.url,
        use_type=ChkUseType("operational"),
        metadata=MetadataModel(mail_id=str(mail.pk)),
    )
    with ApiClient(Configuration(username=settings.LOB_SECRET_KEY)) as client:
        check = ChecksApi(client).create(
            check_editable,
            idempotency_key=idempotency_key,
            _request_timeout=TIMEOUT,
        )
    mr_check = Check.objects.create(
        number=check.check_number,
        agency=comm.foia.agency,
        amount=amount,
        communication=comm,
        user=User.objects.get(username="MuckrockStaff"),
    )
    mr_check.send_email()
    return check
