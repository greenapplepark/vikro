from . import BaseComponent, COMPONENT_TYPE_AMQP
from gevent import monkey
monkey.patch_all
import kombu
import gevent
import Queue
import socket

class RabbitMQComponent(BaseComponent):
    
    def __init__(self, config, service):
        self.component_type = COMPONENT_TYPE_AMQP
        self._connection = kombu.Connection('amqp://keke:keke@192.168.1.88:5672/')
        exchange_name = 'service_{0}_exchange'.format(type(service).__name__)
        queue_name = 'service_{0}_queue'.format(type(service).__name__)
        self._service_exchange = self._make_exchange(exchange_name, type='direct')
        self._service_queue = self._make_queue(queue_name, self._service_exchange)
        self._parent_service = service

    def initialize(self):
        try:
            self._connection.connect()
            gevent.spawn(self._listener)
        except Exception, e:
            print e
            print 'Failed to connect to rabbitmq server'

    def finalize(self):
        self._connection.release()

    def _listener2(self):
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

    def _listener(self):
        while self.is_connected() == False:
            print "waiting for connection"
            gevent.sleep(1)
        with self._connection.Consumer(queues=self._service_queue, callbacks=[self._on_request]):
            while True:
                try:
                    self._connection.drain_events(timeout=1)
                except socket.timeout:
                    pass
                except KeyboardInterrupt:
                    return
                except Exception, e:
                    print e
                    return

    def is_connected(self):
        return self._connection

    def _make_exchange(self, name, type='direct'):
        return kombu.Exchange(name, type)

    def _make_queue(self, name, exchange):
        return kombu.Queue(name, exchange)

    def _on_request(self, request, message):
        print 'got message222!!! %s' % message.payload