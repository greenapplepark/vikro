"""
vikro.exceptions
~~~~~~~~~~~~~~~~

This module contains the set of Vikro' exceptions.
"""

class VikroException(Exception):
    """Base exception of all vikro exceptions."""

class VikroAMQPDisconnectedException(VikroException):
    """AMPQ is disconnected."""

class VikroTimeoutException(VikroException):
    """RPC request timeout."""

class VikroPartiallyDoneException(VikroException):
    """The request is partially done due to failure of some sub request to other services."""

class VikroMethodNotFoundException(VikroException):
    """The request method is not found."""
