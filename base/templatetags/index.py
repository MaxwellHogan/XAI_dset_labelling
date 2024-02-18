# https://docs.djangoproject.com/en/dev/howto/custom-template-tags/

from django import template
register = template.Library()

@register.filter
def index(indexable, i):
    return indexable[i]