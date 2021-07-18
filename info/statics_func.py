from . import models


def add_to_session(session, action_message, action_input):
    user_activities = session.get("user_activities", [])

    user_activities.append(
        (action_input, action_message)
    )

    session["user_activities"] = user_activities
    session.save()


def phone_number_exists_or_not(request):
    phone_number = request.POST.get("phone_number", None)
    phone_number_qs = models.PhoneBook.objects.filter(user=request.user.id).filter(phone_number=phone_number)

    if not phone_number_qs:
        return True
    else:
        return False

