"""
vikro.components.cache
~~~~~~~~~~~~~~~~~~~~~~

This module provides build-in cache support for vikro.
"""

from vikro.components import BaseComponent

class CacheComponent(BaseComponent):
    """Cache support for vikro."""

    def __init__(self):
        super(CacheComponent, self).__init__()

    def initialize(self):
        pass

    def finalize(self):
        pass

    @property
    def component_type(self):
        return self._component_type
