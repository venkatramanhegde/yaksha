from rest_framework import serializers
from .models import User


class LoginSerializer(serializers.Serializer):
    """This is the serializer used for logging in user"""
    phone_no = serializers.CharField(max_length=25, required=True)
    password = serializers.CharField(
        style={'input_type': 'password'},  write_only=True, required=True
    )

    class Meta:
        model = User
        fields = ('phone_no', 'password')


class SignUpSerializer(serializers.Serializer):
    """This is the serializer used for signup in user"""
    name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(max_length=100, required=True)
    phone_number = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True, required=True
    )

    class Meta:
        model = User,

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data.get("password"))
        user.save()
        return user


