class VikroException(Exception):
    pass

class VikroTimeoutException(VikroException):
    pass

class VikroPartiallyDoneException(VikroException):
    pass

class VikroMethodNotFoundException(VikroException):
    pass