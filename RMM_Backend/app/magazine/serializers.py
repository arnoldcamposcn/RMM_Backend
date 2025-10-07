from rest_framework import serializers
from .models import Ediciones, Newsletter, Contacto

class EdicionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ediciones
        fields = "__all__"


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = "__all__"

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contacto
        fields = "__all__"

