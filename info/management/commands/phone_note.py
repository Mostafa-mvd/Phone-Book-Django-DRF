import json
import platform
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from info import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('user', nargs=1, type=int)

    def handle(self, *args, **options):
        path_to_save = ""
        phone_numbers_dict = {}

        if options["user"]:
            user_model = get_user_model()
            for arg in options["user"]:
                try:
                    user = user_model.objects.get(pk=arg)
                    phone_numbers = models.PhoneBook.objects.filter(user=user)
                    phone_numbers_dict[str(user)] = {}
                    os_name = platform.system()

                    for item in phone_numbers:
                        phone_numbers_dict[str(user)][str(item)] = {}
                        phone_numbers_dict[str(user)][str(item)]["phone_number"] = item.phone_number

                    if os_name == "Linux":
                        path_to_save = f"{settings.BASE_DIR}/user_phone_notes_json/"
                    elif os_name == "Window":
                        path_to_save = f"{settings.BASE_DIR}\\user_phone_notes_json\\"

                    with open(f'{path_to_save}{str(user)}_phone_note.json', 'w') as file_handler:
                        json.dump(phone_numbers_dict, file_handler, indent=2)

                except user_model.DoesNotExist:
                    print("User pk does not exits.")

        self.stdout.write(self.style.SUCCESS('Successfully done'))
