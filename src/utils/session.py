import requests


def get_session(*args, **kwargs):
    """Get requests session, setting global config on here.

    Returns:
        [requests.seesion]: Requests session.
    """
    session = requests.session(*args, **kwargs)

    return session
