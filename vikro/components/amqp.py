from . import BaseComponent, COMPONENT_TYPE_AMQP
from gevent import monkey
monkey.patch_all
import kombu
import gevent
import Queue
import socket

class AMQPComponent(BaseComponent):
    
    def __init__(self, service, server_address, server_port, username, password):
        self._component_type = COMPONENT_TYPE_AMQP
        self._url = 'amqp://{}:{}@{}:{}/'.format(username, password, server_address, server_port)
        self._connection = kombu.Connection(self._url)
        exchange_name = 'service_{0}_exchange'.format(type(service).__name__)
        queue_name = 'service_{0}_queue'.format(type(service).__name__)
        self._service_exchange = self.make_exchange(exchange_name, type='direct')
        self._service_queue = self.make_queue(queue_name, self._service_exchange)
        self._parent_service = service

    def initialize(self):
        try:
            self._connection.connect()
            # gevent.spawn(self._listener)
        except Exception, e:
            print 'Failed to connect to AMQP server {}'.format(self._url), e

    def run(self):
        gevent.spawn(self._listener)

    def finalize(self):
        self._connection.release()

    @property
    def component_type(self):
        return self._component_type

    def _listener(self):
        while self.is_connected() == False:
            print "waiting for connection"
            gevent.sleep(1)
        with self._connection.Consumer(queues=self._service_queue, callbacks=[self._on_request]):
            while self._parent_service.is_running:
                try:
                    self._connection.drain_events(timeout=1)
                except socket.timeout:
                    pass
                except KeyboardInterrupt:
                    return
                except Exception, e:
                    print e
                    return
                gevent.sleep(1)

    def is_connected(self):
        return self._connection.connected

    def make_exchange(self, name, type='direct', durable=True, auto_delete=False):
        return kombu.Exchange(name, type, durable=durable, auto_delete=auto_delete)

    def make_queue(self, name, exchange, durable=True, auto_delete=False):
        return kombu.Queue(name, exchange, durable=durable, auto_delete=auto_delete)

    def _on_request(self, request, message):
        print 'got message222!!! %s' % message.payload