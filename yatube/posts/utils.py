from django.conf import settings
from django.core.paginator import Paginator


def paginator_obj(request, list):
    paginator = Paginator(list, settings.POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
