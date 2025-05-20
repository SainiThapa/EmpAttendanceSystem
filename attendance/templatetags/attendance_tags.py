from django import template

register = template.Library()

@register.filter
def format_hours(value):
    if value is None:
        return "-"
    hours = int(value)
    minutes = int((value - hours) * 60)
    if hours == 0 and minutes == 0:
        return "0 minutes"
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    return " ".join(parts) or "0 minutes"