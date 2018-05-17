"""
This is the logic for handling web form submissions.  The initial request is to
be manually sent through a web form, and then all following communications are
handled as if there were no portal
"""

# MuckRock
from muckrock.portal.portals.manual import ManualPortal


class WebFormPortal(ManualPortal):
    """A portal which is just a web form submission"""

    def send_msg(self, comm, **kwargs):
        """The initial message should create a portal task, all others will use
        any other contact info available
        """
        super(WebFormPortal, self).send_msg(comm, **kwargs)
        comm.foia.portal = None
        comm.foia.save(comment='web form portal self removing')
