import ast
import json
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from info.models import PhoneBook


class PhoneBookTestCase(TestCase):

    # before every test
    def setUp(self):
        self.testcase_dict = json.load(open("../testcase.json"))
        self.login_requirement = self.testcase_dict["login_requirements"][0]
        self.client = Client()  # Our Dummy Browser
        self.user = get_user_model().objects.create_user(**self.login_requirement)
        self.client.post(reverse('user:login'), data=self.login_requirement)

    # after every test
    def tearDown(self):
        self.client.get(reverse("user:logout"))

    def test_a_add_number_successfully(self):
        response = self.client.post(reverse("info:add_info"), data={
            "first_name": "mostafa",
            "last_name": "hamidi",
            "phone_number": "09384485325"
        })
        self.assertEqual(response.status_code, 200)

    def test_b_add_number_unsuccessfully(self):
        incorrect_phone_numbers = self.testcase_dict["incorrect_phone_numbers"]
        correct_phone_number = self.testcase_dict["users_phone_numbers"][0]

        PhoneBook.objects.create(user=self.user, **correct_phone_number).save()

        for phone_info in incorrect_phone_numbers:
            response = self.client.post(reverse("info:add_info"), data=phone_info)
            self.assertEqual(response.status_code, 201)

    def test_c_search_phone_number(self):
        phone_numbers = self.testcase_dict["users_phone_numbers"]

        for phone_number in phone_numbers:
            PhoneBook.objects.create(user=self.user, **phone_number).save()

        # Test 1: completed phone number that doesn't exist
        response = self.client.get(reverse("info:search"), data={
            "phone_number": "09383385338",
            "checked_radio_box_number": "1"
        })

        content = ast.literal_eval(response.content.decode("UTF-8"))  # convert bytecode to python dict
        self.assertEqual(content["results_count"], 0)

        # Test 2: completed phone number that exists
        response = self.client.get(reverse("info:search"), data={
            "phone_number": phone_numbers[2]["phone_number"],
            "checked_radio_box_number": "1"
        })
        content = ast.literal_eval(response.content.decode("UTF-8"))
        self.assertEqual(content["results_count"], 1)

        # Test 3: start with
        response = self.client.get(reverse("info:search"), data={
            "phone_number": "0938",
            "checked_radio_box_number": "2"
        })
        content = ast.literal_eval(response.content.decode("UTF-8"))
        self.assertEqual(content["results_count"], 3)

        # Test 4: end with
        response = self.client.get(reverse("info:search"), data={
            "phone_number": "25",
            "checked_radio_box_number": "3"
        })
        content = ast.literal_eval(response.content.decode("UTF-8"))
        self.assertEqual(content["results_count"], 4)

        # Test 4: contain
        response = self.client.get(reverse("info:search"), data={
            "phone_number": "458",
            "checked_radio_box_number": "4"
        })
        content = ast.literal_eval(response.content.decode("UTF-8"))
        self.assertEqual(content["results_count"], 2)

        # Test 3: start with
        response = self.client.get(reverse("info:search"), data={
            "phone_number": "34534",
            "checked_radio_box_number": "2"
        })
        content = ast.literal_eval(response.content.decode("UTF-8"))
        self.assertEqual(content["results_count"], 0)

    def test_d_update_phone_number(self):
        phone_number = PhoneBook.objects.create(user=self.user,
                                                first_name="mostafa",
                                                last_name="vahdani",
                                                phone_number="09384475443")

        # Test 1
        response = self.client.post(reverse("info:update"))
        self.assertEqual(response.status_code, 404)  # pk is None

        # Test 2
        response = self.client.post(reverse("info:update") + "?pk=5")
        self.assertEqual(response.status_code, 404)  # pk doesn't exist

        # Test 3
        response = self.client.post(reverse("info:update") + "?pk=sdf")
        self.assertEqual(response.status_code, 404)  # pk is not digit

        # Test 4
        response = self.client.post(reverse("info:update") + f"?pk={phone_number.pk}", data={"phone_number": ""})
        self.assertEqual(response.status_code, 422)

        # Test 5
        response = self.client.post(reverse("info:update") + f"?pk={phone_number.pk}", data={"phone_number": "sdfsd"})
        self.assertEqual(response.status_code, 422)

        # Test 6
        response = self.client.post(reverse("info:update") + f"?pk={phone_number.pk}",
                                    data={"phone_number": "09384475442"})
        self.assertEqual(response.status_code, 200)

        # Test 7
        self.client.post(reverse("info:update") + f"?pk={phone_number.pk}", data={"phone_number": "09384475444"})
        response = self.client.get(reverse("info:show_info"))
        self.assertEqual(response.context_data["object_list"][0].phone_number, "09384475444")

        # Test 8
        login_requirements = self.testcase_dict["login_requirements"][1]
        user_obj = get_user_model().objects.create_user(**login_requirements)
        phone_number = PhoneBook.objects.create(user=user_obj,
                                                first_name="ali",
                                                last_name="ghasemi",
                                                phone_number="09355575443")

        response = self.client.post(reverse("info:update") + f"?pk={phone_number.pk}",
                                    data={"phone_number": "09355575442"})
        self.assertEqual(response.status_code, 404)

    def test_e_show_numbers(self):
        phone_numbers = self.testcase_dict['users_phone_numbers']

        for phone_number in phone_numbers:
            PhoneBook.objects.create(user=self.user, **phone_number).save()

        # Test 1
        response = self.client.get(reverse("info:show_info"))
        self.assertEqual(len(response.context_data["object_list"]), 3)
        self.assertEqual(response.status_code, 200)

        # Test 2
        response = self.client.get(reverse("info:show_info") + "?page=1")
        self.assertEqual(len(response.context_data["object_list"]), 3)
        self.assertEqual(response.status_code, 200)

        # Test 3
        response = self.client.get(reverse("info:show_info") + "?page=2")
        self.assertEqual(len(response.context_data["object_list"]), 2)
        self.assertEqual(response.status_code, 200)

        # Test 4
        response = self.client.get(reverse("info:show_info") + "?page=3")
        self.assertEqual(response.status_code, 404)

        # Test 5
        response = self.client.get(reverse("info:show_info") + "?page=-1")
        self.assertEqual(response.status_code, 404)

        # Test 5
        response = self.client.get(reverse("info:show_info") + "?page=sdfsf")
        self.assertEqual(response.status_code, 404)
