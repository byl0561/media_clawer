import mimetypes

from django.http import JsonResponse, Http404, HttpResponse

from book.utils.local_book import *
from book.utils.douban_book import *
from book.utils.common import *
from utils.file_utils import read_image_file


def diff_douban_250(request):
    douban_250_books = crawl_douban_250()
    local_books = crawl_local(book_folder)
    missing_books = get_missing_books(douban_250_books, local_books)
    extra_books = get_missing_books(local_books, douban_250_books)

    return JsonResponse({
        'missing_books': [missing_book.to_dict() for missing_book in missing_books],
        'extra_books': [extra_book.to_dict() for extra_book in extra_books
                        if not is_retained_book(extra_book)],
    })


def get_cover(request, image_path):
    full_path = os.path.join(book_folder, image_path)
    if not os.path.splitext(full_path)[0].endswith('cover'):
        raise Http404()

    data = read_image_file(full_path)
    if data is None:
        raise Http404()

    mime_type, _ = mimetypes.guess_type(full_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    return HttpResponse(data, content_type=mime_type)


def is_retained_book(book: Book) -> bool:
    return True
