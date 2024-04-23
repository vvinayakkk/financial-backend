from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'contact', 'dob', 'monthlyIncome', 'gender']
        extra_kwargs = {
            'password': {'write_only': True},
            'contact': {'required': True},
            'dob': {'required': True},
            'gender': {'required': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        monthly_income = validated_data.get('monthlyIncome', 0)  # Default to 0 if not provided
        validated_data['monthlyIncome'] = monthly_income
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

