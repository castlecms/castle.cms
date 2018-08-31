from zope.interface import Interface


class IAuthenticator(Interface):

    def __init__(context, request):
        pass

    def change_password(member, new_password):
        pass

    def issue_country_exception(user, country):
        pass

    def login(user):
        pass

    def authenticate(username=None, password=None, country=None, login=True):
        pass

    def issue_2factor_code(username):
        pass

    def authorize_2factor(username, code):
        pass

    def get_supported_auth_schemes():
        pass
