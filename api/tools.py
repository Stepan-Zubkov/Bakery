import jwt
import os
from werkzeug.datastructures import FileStorage

from .models import ErrorModel


def is_allowed(filename: str) -> bool:
    """Check image extension and return boolean

    Args:
        filename (str): name of file

    Returns:
        bool: filename is valid image (png or jpg)
    """
    _, ext = os.path.splitext(filename.lower())
    if ext[1:] in ['png', 'jpg']:
        return True
    return False


def check_jwt(token: str, secret_key: str, password: str) -> bool:
    """Check jwt token and return boolean

    Args:
        token (str): token to check
        secret_key (str): secret_key to decode key
        password (str): password in token body to check
    Returns:
        bool: token is valid
    """
    try:
        data = jwt.decode(
            token, secret_key,
            algorithms=['HS256']
        )

        assert data['password'] == password

    except Exception:
        return False
    return True


def check_image(image: FileStorage) -> dict | None:
    if image and not is_allowed(image.filename):
        return ErrorModel(
            source='image',
            type='type_error.image',
            description=('extension is not allowed.'
                         ' Please upload only .png or .jpg files.')
        ).dict()
