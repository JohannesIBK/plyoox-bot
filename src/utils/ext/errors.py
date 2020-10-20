class FakeArgument:
    def __init__(self, name):
        self.name = name

class ModeratorCommand(Exception):
    pass