from rest_framework import serializers
from .models import PhoneBook


class PhoneNumberSerializer(serializers.ModelSerializer):
    # representation from calling a method -> get_created_time
    created_time = serializers.SerializerMethodField()

    def get_created_time(self, obj):
        return obj.created_time.strftime('%B %d %Y - %H:%M:%S')
    
    def create(self, validated_data):
        """Add user to validated_data dict for accessing user_id for CROD operation"""

        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    class Meta:
        model = PhoneBook
        fields = [
            "pk",
            "first_name",
            "last_name",
            "phone_number",
            "created_time"
        ]
