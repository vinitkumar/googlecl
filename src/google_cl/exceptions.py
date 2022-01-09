class GoogleCLException(Exception):
    pass

class ExecutionError(GoogleCLException):
    pass

class EarlyQuitException(GoogleCLException):
    pass
