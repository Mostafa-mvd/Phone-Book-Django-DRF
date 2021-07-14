from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import ForeignKey
from django.utils.translation import gettext_lazy as _


phone_regex = RegexValidator(regex='^0[0-9]{2,}[0-9]{7,}$', message='phone number invalid')


class PhoneBook(models.Model):
    auto_increment_id = models.AutoField(primary_key=True, verbose_name=_("Auto Increment Id"))
    user = ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name=_("User"))
    first_name = models.CharField(max_length=25, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=25, verbose_name=_("Last Name"))
    phone_number = models.CharField(verbose_name=_("Phone Number"), max_length=11, validators=[phone_regex])
    created_time = models.DateTimeField(verbose_name=_("Created Time"), auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)
