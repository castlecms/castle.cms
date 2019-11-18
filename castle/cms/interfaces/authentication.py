from zope.interface import Interface


class IAuthenticator(Interface):

    def __init__(context, request):
        pass

    def get_secure_flow_key(username=None):
        pass

    def get_secure_flow_state(username=None):
        pass

    def set_secure_flow_state(username=None, state='requesting-auth-code'):
        pass

    def change_password(member, new_password):
        pass

    def issue_country_exception_request(user, country):
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

    def get_options():
        pass
