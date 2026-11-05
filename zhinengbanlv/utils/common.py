from datetime import datetime


def get_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

