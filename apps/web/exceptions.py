class InvalidCredentialsException(Exception):
    def __init__(self, message="Incorrect credentials, please try again."):
        self.message = message
        super().__init__(self.message)


class NotEnoughInventoryException(Exception):
    def __init__(self, message="Not enough stock available, try again later."):
        self.message = message
        super().__init__(self.message)