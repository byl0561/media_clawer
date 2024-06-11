from django.http import JsonResponse

from constant import book_folder
from book.utils.local_book import *
from book.utils.douban_book import *
from book.utils.common import *


def diff_douban_250(request):
    douban_250_books = crawl_douban_250()
    local_books = crawl_local(book_folder)
    missing_books = get_missing_books(douban_250_books, local_books)
    extra_books = get_missing_books(local_books, douban_250_books)

    return JsonResponse({
        'missing_books': [missing_book.to_dict() for missing_book in missing_books],
        'extra_books': [extra_book.to_dict() for extra_book in extra_books],
    })
