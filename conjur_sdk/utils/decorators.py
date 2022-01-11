from conjur_sdk.errors.errors import HttpStatusError, ResourceNotFoundException


def conjur_enterprise_functionality(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpStatusError as err:
            if err.status == 404:
                exception_details = f"{func.__name__} is a Conjur Enterprise feature only. Make sure " \
                                    f"ConjurrcData.conjur_url is valid and you are working against " \
                                    f"Conjur Enterprise server"
                raise ResourceNotFoundException(exception_details) from err
            else:
                raise

    return wrapper
