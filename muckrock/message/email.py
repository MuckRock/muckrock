"""
Provides a base email class for messages.
"""

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class TemplateEmail(EmailMultiAlternatives):
    """
    The TemplateEmail class provides a base for our transactional emails.
    It supports sending a templated email to a user and providing extra template context.
    It always adds the MuckRock diagnostic email as a BCC'd address.
    Both a HTML and a text template should be provided by subclasses or instances.
    The summary attribute is blank by default and is a hack to populate the "email preview"
    display within some (not all) email clients.
    Subjects are expected to be provided at initialization, however a subclass may provide
    a static subject attribute if it is provided to the super __init__ method as as kwarg.
    """

    user = None
    text_template = None
    html_template = None
    summary = ""

    def __init__(self, user=None, **kwargs):
        """Sets the universal attributes for all our email."""
        # Pop our expected keyword arguments to prevent base class init errors
        extra_context = kwargs.pop("extra_context", None)
        text_template = kwargs.pop("text_template", None)
        html_template = kwargs.pop("html_template", None)
        summary = kwargs.pop("summary", None)
        # Initialize the base class
        super(TemplateEmail, self).__init__(**kwargs)
        # Set the fields for the TemplateEmail
        if user:
            if isinstance(user, User):
                self.user = user
                self.to.append(user.email)
            else:
                raise TypeError('"user" argument expects a User type')
        if summary:
            if isinstance(summary, str):
                self.summary = summary
            else:
                raise TypeError('"summary" argument must be a string')
        if text_template:
            self.text_template = text_template
        if html_template:
            self.html_template = html_template
        context = self.get_context_data(extra_context)
        content = {
            "text": render_to_string(self.get_text_template(), context),
            "html": render_to_string(self.get_html_template(), context),
        }
        self.bcc.append(settings.DIAGNOSTIC_EMAIL)
        self.body = content["text"]
        self.attach_alternative(content["html"], "text/html")

    def get_context_data(self, extra_context):
        """Sets basic context data and allow extra context to be passed in."""
        context = {
            "base_url": "https://www.muckrock.com",
            "summary": self.summary,
            "subject": self.subject,
            "user": self.user,
        }
        if extra_context:
            if isinstance(extra_context, dict):
                context.update(extra_context)
            else:
                raise TypeError('"extra_context" must be a dictionary')
        return context

    def get_text_template(self):
        """Returns the template specified by the subclass."""
        if self.text_template is None:
            raise NotImplementedError("A text template must be provided.")
        return self.text_template

    def get_html_template(self):
        """Returns the template specified by the subclass."""
        if self.html_template is None:
            raise NotImplementedError("An HTML template must be provided.")
        return self.html_template
