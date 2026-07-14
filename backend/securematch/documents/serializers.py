from rest_framework import serializers
from django.core.validators import RegexValidator
from documents.models import Auditor


class AuditorRetrieveSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving Auditor Profile details.
    """

    class Meta:
        model = Auditor
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "designation",
            "public_key",
            "key_version",
            "status",
            "created_at",
            "updated_at",
        )


class AuditorUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Auditor Profile.
    """

    name = serializers.CharField(
        min_length=3,
        max_length=255,
        required=False,
        allow_blank=False,
    )
    email = serializers.EmailField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    phone = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    designation = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    class Meta:
        model = Auditor
        fields = (
            "name",
            "email",
            "phone",
            "designation",
        )

    def validate(self, attrs):
        editable_fields = set(self.Meta.fields)
        submitted_editable_fields = editable_fields.intersection(self.initial_data.keys())

        if "name" in self.initial_data and not str(self.initial_data["name"]).strip():
            raise serializers.ValidationError({"name": "Name cannot be empty."})

        if not submitted_editable_fields:
            raise serializers.ValidationError(
                "At least one editable auditor profile field is required."
            )
        return attrs

    def validate_email(self, value):
        if value:
            instance = self.instance
            queryset = Auditor.objects.filter(email__iexact=value)
            if instance:
                queryset = queryset.exclude(id=instance.id)
            if queryset.exists():
                raise serializers.ValidationError("An auditor with this email already exists.")
        return value

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")

        instance = self.instance
        queryset = Auditor.objects.filter(name__iexact=value.strip())
        if instance:
            queryset = queryset.exclude(id=instance.id)
        if queryset.exists():
            raise serializers.ValidationError("An auditor with this name already exists.")
        return value.strip()


class AuditorStatusSerializer(serializers.Serializer):
    """
    Serializer for updating Auditor status.
    """

    status = serializers.ChoiceField(
        choices=Auditor.STATUS_CHOICES,
        required=True,
        error_messages={
            "invalid_choice": "Invalid status values. Supported values are ACTIVE and DISABLED."
        }
    )
