from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentification backend qui permet la connexion avec email ou username
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if username is None or password is None:
            logger.debug('Authenticate called with missing username or password (username=%r).', username)
            return None

        try:
            # Essayer de trouver l'utilisateur par username ou email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )

            # Log non-sensitive metadata about the provided password for debugging
            try:
                pw_repr = repr(password)
                pw_len = len(password) if password is not None else 0
                pw_hex = password.encode('utf-8')[:64].hex() if password is not None else ''
            except Exception:
                pw_repr = '<unrepresentable>'
                pw_len = 0
                pw_hex = ''
            logger.debug('Password metadata: repr=%s, length=%s, hex_prefix=%s', pw_repr, pw_len, pw_hex)

            pw_ok = user.check_password(password)
            can_auth = self.user_can_authenticate(user)
            logger.debug('Found user=%r (id=%s). check_password=%s, user_can_authenticate=%s', user.username, getattr(user, 'id', None), pw_ok, can_auth)
            if pw_ok and can_auth:
                logger.info('Authentication successful for user=%r', user.username)
                return user
            else:
                logger.info('Authentication failed for user=%r: pw_ok=%s, can_auth=%s', user.username, pw_ok, can_auth)

        except User.DoesNotExist:
            # Ne pas révéler si l'utilisateur existe ou non
            logger.debug('Authenticate: no user matches %r', username)
            return None

        return None