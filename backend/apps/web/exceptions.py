from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class InvalidCredentialsException(APIException):
    status_code = 400
    default_detail = 'Incorrect credentials, please try again'


class NotEnoughInventoryException(APIException):
    status_code = 400
    default_detail = 'Not enough stock available, try again later'


class ValidationException(APIException):
    status_code = 400
    default_detail = 'Completed orders cannot be canceled'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, InvalidCredentialsException):
        return Response(
            {'error': str(exc.message)},
            status=status.HTTP_401_UNAUTHORIZED
        )

    return response


