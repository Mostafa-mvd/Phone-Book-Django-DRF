from . import models


def user_phone_finder(request):
    user_phone_book_info = models.PhoneBook.objects.filter(user=request.user.id).all()

    return {
       'all_phones': user_phone_book_info,
    }
