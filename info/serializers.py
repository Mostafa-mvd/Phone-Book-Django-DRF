from rest_framework import serializers
from .models import PhoneBook
from django.contrib.auth import get_user_model


class PhoneNumberSerializer(serializers.ModelSerializer):
    created_time = serializers.SerializerMethodField()

    def get_created_time(self, obj):
        return obj.created_time.strftime('%B %d %Y - %H:%M:%S')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    class Meta:
        model = PhoneBook
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "created_time"
        ]