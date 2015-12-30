"""
General temaplate tags
"""

from django import template
from django.template import Library, Node, TemplateSyntaxError
from django.template.defaultfilters import stringfilter
from django.utils.html import escape

from email.parser import Parser
import re

from muckrock.forms import TagManagerForm
from muckrock.settings import STATIC_URL

register = Library()

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

class TableHeaderNode(Node):
    """Tag to create table headers"""

    def __init__(self, get, args):
        # pylint: disable=super-init-not-called
        self.get = get
        self.args = args

    def render(self, context):
        """Render the table headers"""

        get = self.get.resolve(context, True)

        def get_args(*args):
            """Append get args to url if they are present"""
            return ''.join('&amp;%s=%s' % (arg, escape(get[arg])) for arg in args if arg in get)

        html = ''
        for width, field in self.args:
            field = field.resolve(context, True)
            html += '<th width="%s%%">' % width
            if field:
                if get.get('field') == field and get.get('order') == 'asc':
                    order = 'desc'
                    img = '&nbsp;<img src="%simg/down-arrow.png" />' % STATIC_URL
                elif get.get('field') == field and get.get('order') == 'desc':
                    order = 'asc'
                    img = '&nbsp;<img src="%simg/up-arrow.png" />' % STATIC_URL
                else:
                    order = 'asc'
                    img = ''
                html += '<a href="?order=%s&amp;field=%s%s">%s%s</a>' % \
                        (order, field, get_args('page', 'per_page'), field.capitalize(), img)
            html += '</th>'
        return html

@register.tag
def table_header(parser, token):
    """Tag to create table headers"""

    get = token.split_contents()[1]
    bits = token.split_contents()[2:]
    if len(bits) % 2 != 0:
        raise TemplateSyntaxError("'table_header' statement requires matching number "
                                  "of width and fields")
    bits = zip(*[bits[i::2] for i in range(2)])
    return TableHeaderNode(parser.compile_filter(get),
                           [(a, parser.compile_filter(b)) for a, b in bits])

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

@register.filter
def redact_emails(text):
    """Redact emails from text"""
    return email_re.sub(email_redactor, text)

@register.filter
def redact_list(obj_list, user):
    """
    Filters and returns a list of objects based on whether they should be visible
    to the currently-logged in user.
    """
    redacted_list = []
    for item in obj_list:
        try:
            if item.object.viewable_by(user):
                redacted_list.append(item)
        except AttributeError:
            redacted_list.append(item)
    return redacted_list

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

@register.assignment_tag
def editable_by(foia, user):
    """Template tag to call editable by on FOIAs"""
    return foia.editable_by(user)

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

