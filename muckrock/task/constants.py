"""Constants for the Task Application"""

SNAIL_MAIL_CATEGORIES = [
    ("a", "Appeal"),
    ("n", "New"),
    ("u", "Update"),
    ("f", "Followup"),
    ("p", "Payment"),
]
PORTAL_CATEGORIES = [("i", "Incoming")] + SNAIL_MAIL_CATEGORIES
PUBLIC_FLAG_CATEGORIES = [
    ("move communication", "A communication ended up on this request inappropriately."),
    ("no response", "This agency has not responded after multiple submissions."),
    (
        "wrong agency",
        "The agency has indicated that this request should be directed to "
        "another agency.",
    ),
    (
        "missing documents",
        "The agency mailed documents but I do not see them on this request",
    ),
    ("portal help", "I need help with a portal, link or login"),
    ("form", "The agency has asked that I fill out or sign a PDF form."),
    ("follow-up complaints", "Agency is complaining about follow-up messages."),
    ("appeal", "Should I appeal this response?"),
    ("proxy", "The agency denied the request due to an in-state citzenship law."),
]
PRIVATE_FLAG_CATEGORIES = [
    ("contact info changed", "User supplied contact info."),
    ("no proxy", "No proxy was available."),
    ("agency login confirm", "An agency used a secure login to update a request."),
    ("agency login validate", "An agency used an insecure login to update a request."),
    ("agency new email", "An agency with no primary email set replied via email."),
    (
        "manual form",
        "A request needs a PDF form to be manually filled out to be submitted",
    ),
    ("foiaonline", "The FOIAOnline autologin failed"),
    ("download file", "This request contains a link to a file to download"),
]
AGENCY_FLAG_CATEGORIES = [
    ("already responded", "I already responded to this request"),
    ("bad contact", "I am not the best contact for this request"),
    ("wrong agency", "This request should go to a different agency"),
]
FLAG_CATEGORIES = (
    PUBLIC_FLAG_CATEGORIES + PRIVATE_FLAG_CATEGORIES + AGENCY_FLAG_CATEGORIES
)
