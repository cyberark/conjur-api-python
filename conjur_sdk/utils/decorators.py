from conjur_sdk.errors.errors import HttpStatusError, ResourceNotFoundException


def conjur_enterprise_functionality(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpStatusError as err:
            if err.status == 404:
                exception_details = "/info is Conjur Enterprise feature only. Make sure ConjurrcData.conjur_url " \
                                    "is valid and you are working against Conjur Enterprise server"
                raise ResourceNotFoundException(exception_details) from err
            else:
                raise

    return wrapper
