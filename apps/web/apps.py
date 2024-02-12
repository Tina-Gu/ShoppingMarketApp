from django.apps import AppConfig
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from apps.web.exceptions import InvalidCredentialsException


class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.web'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, InvalidCredentialsException):
        return Response(
            {'error': str(exc.message)},
            status=status.HTTP_401_UNAUTHORIZED
        )

    return response

