from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """ Custom filter to get an item from a dictionary using a key. """
    return dictionary.get(key, "")
