"""
vikro.exceptions
~~~~~~~~~~~~~~~~

This module contains the set of Vikro' exceptions.
"""

class VikroException(Exception):
    """Base exception of all vikro exceptions."""

class VikroAMQPDisconnected(VikroException):
    """AMPQ is disconnected."""

class VikroRPCTimeout(VikroException):
    """RPC request timeout."""

class VikroPartiallyDone(VikroException):
    """The request is partially done due to failure of some sub request to other services."""

class VikroMethodNotFound(VikroException):
    """The request method is not found."""

class VikroInvalidParam(VikroException):
    """The paramteres is invalid when calling api."""

class VikroNoPermission(VikroException):
    """No permission to call."""

class VikroTooManyRequests(VikroException):
    """Too many requests."""

EXCEPTION_CODE_MAPPING = {
    VikroPartiallyDone: '206',
    VikroMethodNotFound: '404',
    VikroInvalidParam: '400',
    VikroNoPermission: '401',
    VikroTooManyRequests: '429',
}
