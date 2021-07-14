import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from info.models import PhoneBook


class ShowActivitiesTestCase(TestCase):

    def setUp(self) -> None:
        self.testcase = json.load(open("../testcase.json"))
        self.login_requirement = self.testcase["login_requirements"][0]
        self.user = get_user_model().objects.create_user(**self.login_requirement)
        self.client.post(reverse('user:login'), data=self.login_requirement)

    def tearDown(self):
        self.client.get(reverse("user:logout"))

    def test_a_user_activities(self):
        # Test 1
        response = self.client.get(reverse("home:activities"))
        self.assertFalse(response.context_data["activities"])

        # Test 2
        phone_numbers = self.testcase["users_phone_numbers"]

        for phone_number in phone_numbers:
            PhoneBook.objects.create(user=self.user, **phone_number).save()

        self.client.post(reverse("info:add_info"), data={
            "first_name": "mostafa",
            "last_name": "hamidi",
            "phone_number": "09384482715"
        })

        self.client.post(reverse("info:add_info"), data={
            "first_name": "mostafa",
            "last_name": "hamidi",
            "phone_number": "09394586987"
        })

        self.client.get(reverse("info:search"), data={
            "phone_number": "09383385338",
            "checked_radio_box_number": "1"
        })

        self.client.get(reverse("info:search"), data={
            "phone_number": "25",
            "checked_radio_box_number": "3"
        })

        self.client.post(reverse("info:update") + "?pk=1",
                         data={"phone_number": "09384475442"})

        response = self.client.get(reverse("home:activities"))
        self.assertEqual(len(response.context_data["activities"]), 5)
