"""
Custom template tags for rendering actions
"""

from django import template

from actstream.templatetags.activity_tags import AsNode

register = template.Library()


class Action(AsNode):
    """Basic action rendering"""
    template = 'lib/pattern/actions/base.html'

    def render_result(self, context):
        """Renders actions using our own template"""
        action_instance = self.args[0].resolve(context)
        return template.loader.render_to_string(self.template,
                                                {'action': action_instance},
                                                context)


class PassiveAction(Action):
    """Renders an action with emphasis on the object"""
    template = 'lib/pattern/actions/passive.html'


@register.tag
def display_action(parser, token):
    """Renders the template for the action description"""
    return Action.handle_token(parser, token)

@register.tag
def display_passive_action(parser, token):
    """Renders the template for the passive action"""
    return PassiveAction.handle_token(parser, token)
