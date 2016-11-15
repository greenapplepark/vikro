"""
vikro.components module contains some supports for vikro,
including amqp, cache and database.
"""

COMPONENT_TYPE_NONE = 0
COMPONENT_TYPE_AMQP = 1
COMPONENT_TYPE_DATABASE = 2

class BaseComponent(object):
    """Abstract class of all components."""

    def __init__(self):
        self._component_type = COMPONENT_TYPE_NONE

    def initialize(self):
        """Interface to initialize component."""
        raise NotImplementedError('Subclasses should implement initialize!')

    def finalize(self):
        """Interface to finalize component."""
        raise NotImplementedError('Subclasses should implement finalize!')

    @property
    def component_type(self):
        """Component type."""
        raise NotImplementedError('Subclasses should initialize component_type variable!')

    @component_type.setter
    def component_type(self, value):
        """Component type setter."""
        self._component_type = value
