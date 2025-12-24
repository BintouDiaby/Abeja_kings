from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentification backend qui permet la connexion avec email ou username
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if username is None or password is None:
            return None

        try:
            # Essayer de trouver l'utilisateur par username ou email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )

            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        except User.DoesNotExist:
            # Ne pas révéler si l'utilisateur existe ou non
            return None

        return None