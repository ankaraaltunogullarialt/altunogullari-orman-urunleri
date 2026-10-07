from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """QueryDict içinden dinamik key ile değer al"""
    if dictionary is None:
        return ''
    try:
        value = dictionary.get(key, '')
        return value if value is not None else ''
    except (AttributeError, TypeError):
        return ''


@register.simple_tag(takes_context=True)
def koru_query_params(context, *haric):
    """
    Mevcut query parametrelerini gizli input olarak döndürür.
    'haric' listesindeki parametreler atlanır.
    """
    request = context.get('request')
    if not request:
        return ''
    
    html = []
    for key, value in request.GET.items():
        if key not in haric:
            html.append(
                f'<input type="hidden" name="{key}" value="{value}">'
            )
    return ''.join(html)