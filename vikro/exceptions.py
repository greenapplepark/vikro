class VikroException(Exception):
    pass

class VikroAMQPDisconnectedException(VikroException):
    pass

class VikroTimeoutException(VikroException):
    pass

class VikroPartiallyDoneException(VikroException):
    pass

class VikroMethodNotFoundException(VikroException):
    pass