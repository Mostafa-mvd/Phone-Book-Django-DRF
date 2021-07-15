from django.db.models import fields
from rest_framework import serializers
from .models import PhoneBook
from django.contrib.auth import get_user_model


class AddPhoneNumberSerializer(serializers.ModelSerializer):
    
    user = serializers.SlugRelatedField(
        queryset=get_user_model().objects.all(), slug_field="username"
    )


    created_time = serializers.SerializerMethodField()
    def get_created_time(self, obj):
        return obj.created_time.strftime('%B %d %Y - %H:%M:%S')


    class Meta:
        model = PhoneBook
        fields = [
            'user',
            "first_name",
            "last_name",
            "phone_number",
            "created_time"
        ]