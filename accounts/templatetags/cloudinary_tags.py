from django import template

register = template.Library()

@register.filter
def fix_pdf_url(url):
    return url  # just return as-is for now