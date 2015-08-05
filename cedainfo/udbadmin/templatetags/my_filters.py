from django import template
register = template.Library()

#
# This is just so I can do a dictionary lookup in a template. See
# http://stackoverflow.com/questions/8000022/django-template-how-to-lookup-a-dictionary-value-with-a-variable
#
@register.filter(name='lookup')
def cut(value, arg):
    return value[arg]
