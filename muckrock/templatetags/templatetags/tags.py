"""
General temaplate tags
"""

from django import template
from django.conf import settings
from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.html import escape
from django.utils.safestring import mark_safe

import bleach
from email.parser import Parser
import markdown
import re
from urllib import urlencode

from muckrock.forms import NewsletterSignupForm, TagManagerForm
from muckrock.project.forms import ProjectManagerForm

register = Library()

@register.simple_tag
def autologin(user):
    """Generate an autologin token for the user."""
    if user.is_authenticated():
        return urlencode(user.profile.autologin())
    return ''

@register.simple_tag
def active(request, pattern):
    """Check url against pattern to determine active css attribute"""
    pattern = pattern.replace('{{user}}', str(request.user))
    if re.search(pattern, request.path):
        return 'current-tab'
    return ''

@register.simple_tag
def page_link(request, page_num):
    """Generates a pagination link that preserves context"""
    query = request.GET
    href = '?page=' + str(page_num)
    for key, value in query.iteritems():
        if value and key != u'page':
            href += '&%s=%s' % (key, escape(value))
    return href

@register.filter
@stringfilter
def company_title(companies):
    """Format possibly multiple companies for the title"""
    if '\n' in companies:
        return companies.split('\n')[0] + ', et al'
    else:
        return companies


@register.filter(name='abs')
def abs_filter(value):
    """Absolute value of a number"""
    return abs(value)

email_re = re.compile(r'[a-zA-Z0-9._%+-]+@(?P<domain>[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4})')

def email_redactor(match):
    """Don't redact muckrock emails"""
    if match.group('domain') != 'requests.muckrock.com':
        return match.group(0)
    else:
        return 'requests@muckrock.com'

@register.filter('fieldtype')
def fieldtype(field):
    """Returns the name of the class."""
    return field.field.widget.__class__.__name__

@register.filter
def redact_emails(text):
    """Redact emails from text"""
    return email_re.sub(email_redactor, text)

# http://stackoverflow.com/questions/1278042/
# in-django-is-there-an-easy-way-to-render-a-text-field-as-a-template-in-a-templ/1278507#1278507

@register.tag(name="evaluate")
def do_evaluate(parser, token):
    """
    tag usage {% evaluate object.textfield %}
    """
    # pylint: disable=unused-argument
    try:
        _, variable = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" %
                                           token.contents.split()[0])
    return EvaluateNode(variable)

class EvaluateNode(template.Node):
    """Node for do_evaluate"""
    def __init__(self, variable):
        # pylint: disable=super-init-not-called
        self.variable = template.Variable(variable)

    def render(self, context):
        try:
            content = self.variable.resolve(context)
            tmpl = template.Template(content)
            return tmpl.render(context)
        except (template.VariableDoesNotExist, template.TemplateSyntaxError):
            return 'Error rendering', self.variable

@register.inclusion_tag('tags/tag_manager.html', takes_context=True)
def tag_manager(context, mr_object):
    """Template tag to insert a tag manager component"""
    try:
        tags = mr_object.tags.all()
    except AttributeError:
        tags = None
    try:
        owner = mr_object.user
    except AttributeError:
        owner = None
    is_authorized = context['user'].is_staff or context['user'] == owner
    form = TagManagerForm(initial={'tags': tags})
    return {
        'tags': tags,
        'form': form,
        'is_authorized': is_authorized,
        'endpoint': mr_object.get_absolute_url()
    }

@register.inclusion_tag('project/component/manager.html', takes_context=True)
def project_manager(context, mr_object):
    """Template tag to insert a project manager component"""
    try:
        projects = mr_object.projects.all()
    except AttributeError:
        projects = None
    try:
        owner = mr_object.user
    except AttributeError:
        owner = None
    user = context['user']
    experimental = user.is_authenticated() and user.profile.experimental
    authorized = user.is_staff or (user == owner and experimental)
    form = ProjectManagerForm(initial={'projects': [project.pk for project in projects]})
    return {
        'projects': projects,
        'form': form,
        'authorized': authorized,
        'endpoint': mr_object.get_absolute_url(),
    }

@register.inclusion_tag('lib/social.html', takes_context=True)
def social(context, title=None, url=None):
    """Template tag to insert a sharing widget. If url is none, use the request path."""
    request = context['request']
    title = context.get('title', '') if title is None else title
    url = request.path if url is None else url
    url = 'https://' + request.get_host() + url
    return {
        'request': request,
        'title': title,
        'url': url,
    }

@register.inclusion_tag('lib/newsletter.html', takes_context=True)
def newsletter(context, list_id=None, label=None, cta=None):
    """Template tag to insert a newsletter signup form."""
    list_id = settings.MAILCHIMP_LIST_DEFAULT if list_id is None else list_id
    label = 'Newsletter' if label is None else label
    cta = 'Want the latest investigative and FOIA news?' if cta is None else cta
    is_default = list_id == settings.MAILCHIMP_LIST_DEFAULT
    request = context['request']
    initial_data = {'list': list_id}
    if request.user.is_authenticated():
        initial_data['email'] = request.user.email
    newsletter_form = NewsletterSignupForm(initial=initial_data)
    return {
        'request': request,
        'label': label,
        'cta': cta,
        'is_default': is_default,
        'newsletter_form': newsletter_form
    }

@register.filter
def display_eml(foia_file):
    """Extract text from eml file for display"""
    msg = Parser().parse(foia_file.ffile)
    if msg.get_content_type() == 'text/plain':
        return msg.get_payload(decode=True)
    if msg.get_content_type() == 'multipart/alternative':
        for sub_msg in msg.get_payload():
            if sub_msg.get_content_type() == 'text/plain':
                return sub_msg.get_payload(decode=True)

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary template filter"""
    return dictionary.get(key)

@register.filter
def smartypants(text):
    """Renders typographically-correct quotes with the smartpants library"""
    import smartypants as _smartypants
    smart_text = _smartypants.smartypants(text)
    return mark_safe(bleach.clean(smart_text))

@register.filter(name='markdown')
@stringfilter
def markdown_filter(text, _safe=None):
    """Take the provided markdown-formatted text and convert it to HTML."""
    # First render Markdown
    extensions = [
            'markdown.extensions.smarty',
            'markdown.extensions.tables',
            'pymdownx.magiclink',
            ]
    markdown_text = markdown.markdown(text, extensions=extensions)
    # Next bleach the markdown
    allowed_tags = bleach.ALLOWED_TAGS + [
        u'h1',
        u'h2',
        u'h3',
        u'h4',
        u'h5',
        u'h6',
        u'p',
        u'img',
        u'iframe'
    ]
    allowed_attributes = bleach.ALLOWED_ATTRIBUTES.copy()
    allowed_attributes.update({
        'iframe': ['src', 'width', 'height', 'frameborder', 'marginheight', 'marginwidth'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
    })
    # allows bleaching to be avoided
    if _safe == 'safe':
        bleached_text = markdown_text
    elif _safe == 'strip':
        bleached_text = bleach.clean(
            markdown_text,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True,
        )
    else:
        bleached_text = bleach.clean(
            markdown_text,
            tags=allowed_tags,
            attributes=allowed_attributes
        )
    return mark_safe(bleached_text)
