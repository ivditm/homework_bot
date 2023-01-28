class my_exception(Exception):
    """class of exception."""

    def __init__(self, text):
        """активация класса."""
        self.text = text
