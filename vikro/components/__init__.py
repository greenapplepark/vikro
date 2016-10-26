COMPONENT_TYPE_NONE = 0
COMPONENT_TYPE_AMQP = 1
COMPONENT_TYPE_DATABASE = 2

class BaseComponent(object):
    def __init__(self, config, service):
        raise NotImplementedError('Subclasses should implement __init__!')

    def initialize(self):
        raise NotImplementedError('Subclasses should implement initialize!')

    def finalize(self):
        raise NotImplementedError('Subclasses should implement finalize!')

    @property
    def component_type(self):
        raise NotImplementedError('Subclasses should initialize component_type variable!')

    @component_type.setter
    def component_type(self, value):
        self._component_type = value