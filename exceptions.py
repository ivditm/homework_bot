class MyException(BaseException):
    """class of exception."""

    def __init__(self, text):
        """активация класса."""
        self.text = text


class MyTypeError(TypeError):
    """кастомный класс TypeError."""

    def __init__(self, text):
        """активация класса."""
        self.text = text
