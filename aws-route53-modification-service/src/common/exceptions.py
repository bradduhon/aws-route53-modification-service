

class BadInput(Exception):
    """Raise this exception when input is required to be of a specific value"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        pass