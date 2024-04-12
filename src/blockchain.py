class Blockchain:
    """
    The blockchain of the BlockChat

    Attributes:
        blocks (list): list that contains the validated blocks of the chain.
    """

    def __init__(self):
        """Inits a Blockchain"""
        self.blocks = []

    def __str__(self):
        """Returns a string representation of a Blockchain object"""
        return str(self.__class__) + ": " + str(self.__dict__)

    """ This line defines a special method, __str__(), within a Python class, 
    which is intended to provide a human-readable string representation of an 
    instance of that class. When you define a __str__ method in a class, Python 
    calls this method whenever you use the str() function on an instance of the 
    class or when you attempt to print an instance of the class.

    This __str__ implementation is particularly useful for debugging purposes or 
    when you need a quick overview of an instance's state, as it gives a complete 
    picture of the instance's current attributes and their values."""

    def add_block(self, block):
        """Adds a new block in the chain."""
        self.blocks.append(block)
