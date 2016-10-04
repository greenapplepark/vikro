from . import BaseComponent, COMPONENT_TYPE_AMQP
import kombu
import gevent
import Queue

class RabbitMQComponent(BaseComponent):
    
    def __init__(self, config, service):
        self.component_type = COMPONENT_TYPE_AMQP
        self._connection = kombu.Connection('amqp://keke:keke@192.168.1.88:5672/')
        self._service_exchange = kombu.Exchange(type(service).__name__, type='direct')
        self._service_queue = kombu.Queue(type(service).__name__, self._service_exchange)

    def initialize(self):
        try:
            self._connection.connect()
            gevent.spawn(self._listener)
        except Exception, e:
            print e
            print 'Failed to connect to rabbitmq server'

    def finalize(self):
        self._connection.release()

    def _listener(self):
        while self.is_connected() == False:
            print "waiting for connection"
            gevent.sleep(1)
        with self._connection.SimpleQueue(self._service_queue) as queue:
            while True:
                try:
                    message = queue.get(block=True, timeout=1)
                    if message:
                        print 'got message!!! %s' % message.payload
                        message.ack()
                        if self.is_connected() == False:
                            break
                except KeyboardInterrupt:
                    pass
                except Queue.Empty:
                    pass
                gevent.sleep(1)

    def is_connected(self):
        return self._connection