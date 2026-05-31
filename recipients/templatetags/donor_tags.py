from django import template

register = template.Library()

AVATAR_COLORS = [
    '#e74c3c', '#e67e22', '#f39c12', '#27ae60',
    '#16a085', '#2980b9', '#8e44ad', '#d35400',
    '#c0392b', '#1abc9c', '#2ecc71', '#3498db',
]

@register.filter
def avatar_color(user_id):
    return AVATAR_COLORS[int(user_id) % len(AVATAR_COLORS)]