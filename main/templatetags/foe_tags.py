import six
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def foe_static_repo(path):
    """
    Return the STATIC_REPO and path, similar to the default static tag
    """
    return six.moves.urllib.parse.urljoin(settings.STATIC_REPO, path)