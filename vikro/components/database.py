"""
vikro.components.database
~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides build-in database support for vikro.
"""

from vikro.components import BaseComponent

class DatabaseComponent(BaseComponent):
    """Database support for vikro."""

    def __init__(self):
        super(DatabaseComponent, self).__init__()

    def initialize(self):
        pass

    def finalize(self):
        pass

    @property
    def component_type(self):
        return self._component_type
