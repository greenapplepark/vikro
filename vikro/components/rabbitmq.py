from . import BaseComponent, COMPONENT_TYPE_AMQP
import kombu

class RabbitMQComponent(BaseComponent):
    
    def __init__(self, config):
        self.component_type = COMPONENT_TYPE_AMQP
        self._connection = kombu.Connection('amqp://keke:keke@10.21.100.145:5672/')

    def initialize(self):
        self._connection.connect()

    def finalize(self):
        self._connection.release()