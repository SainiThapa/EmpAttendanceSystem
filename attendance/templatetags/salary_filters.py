# Create this file: attendance/templatetags/salary_filters.py

from django import template

register = template.Library()

@register.filter
def sum_field(queryset, field_name):
    """Sum a specific field from a list of dictionaries"""
    try:
        return sum(item.get(field_name, 0) for item in queryset)
    except (TypeError, AttributeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)

@register.filter
def map_attribute(obj_list, attr_name):
    """Extract attribute values from list of objects/dicts"""
    result = []
    for item in obj_list:
        if isinstance(item, dict):
            result.append(item.get(attr_name, 0))
        else:
            result.append(getattr(item, attr_name, 0))
    return result