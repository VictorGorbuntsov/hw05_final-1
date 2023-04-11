from django.core.paginator import Paginator

from yatube import settings


def paginator(request, posts_list):
    page = Paginator(posts_list, settings.NUMBER_OF_POSTS_IN_PAG)
    page_number = request.GET.get('page')
    return page.get_page(page_number)
