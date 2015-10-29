"""
Custom template tags for rendering actions
"""

from django import template

from actstream.templatetags.activity_tags import AsNode

register = template.Library()


class DisplayAction(AsNode):
    """Basic action rendering"""
    def render_result(self, context):
        """Renders actions using our own template"""
        action_instance = self.args[0].resolve(context)
        return template.loader.render_to_string('actions/base.html',
                                                {'action': action_instance},
                                                context)

@register.tag
def display_action(parser, token):
    """Renders the template for the action description"""
    return DisplayAction.handle_token(parser, token)
