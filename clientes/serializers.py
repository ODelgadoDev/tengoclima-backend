from rest_framework import serializers
from .models import ClientePotencial


class ClientePotencialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientePotencial
        fields = '__all__'