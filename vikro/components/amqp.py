from . import BaseComponent, COMPONENT_TYPE_AMQP
from gevent import monkey
monkey.patch_all
import kombu
import gevent
import Queue
import socket
import logging

logger = logging.getLogger(__name__)

class AMQPComponent(BaseComponent):
    
    def __init__(self, server_address, server_port, username, password):
        self._component_type = COMPONENT_TYPE_AMQP
        self._url = 'amqp://{}:{}@{}:{}/'.format(username, password, server_address, server_port)
        self._connection = kombu.Connection(self._url)
        self._should_keep_connect = False
        self._next_retry = 2

    def initialize(self):
        self._should_keep_connect = True
        try:
            self._connection.connect()
        except Exception, e:
            logger.warning('Failed to connect to AMQP server {}{}'.format(self._url, e))
        gevent.spawn(self.keep_connecting)

    def finalize(self):
        self._should_keep_connect = False
        self._connection.release()

    def get_connection(self):
        return self._connection

    def keep_connecting(self):
        while self._should_keep_connect:
            try:
                if self._connection.connected is True:
                    logger.debug('Connected to {}'.format(self._url))
                    gevent.sleep(10)
                else:
                    if not self._should_keep_connect:
                        break
                    try:
                        logger.debug('Try to reconnect to {}'.format(self._url))
                        self._connection.connect()
                        self._next_retry = 2
                    except Exception, e:
                        gevent.sleep(self._next_retry)
                        self._next_retry = min(self._next_retry * 2, 120)
            except KeyboardInterrupt:
                break

    def listen_to_queue(self, service_name, queue_name, callback, keep_listening=False):
        exchange_name = 'service_{0}_exchange'.format(service_name)
        queue_name = 'service_{0}_queue'.format(service_name)
        exchange = self.make_exchange(exchange_name)
        queue = self.make_queue(queue_name, exchange)
        # always try to listen
        while True:
            while self.is_connected() == False:
                logger.info('waiting for connection')
                gevent.sleep(3)
            conn = self.get_connection() 
            with conn.Consumer(queues=queue, callbacks=[callback]):
                while self._should_keep_connect:
                    try:
                        conn.drain_events(timeout=1)
                    except socket.timeout:
                        pass
                    except KeyboardInterrupt:
                        return
                    except Exception, e:
                        logger.error(e)
                        break
                    gevent.sleep(1)
            if not keep_listening:
                break

    @property
    def component_type(self):
        return self._component_type

    def is_connected(self):
        return self._connection.connected

    def make_exchange(self, name, type='direct', durable=True, auto_delete=True):
        return kombu.Exchange(name, type, durable=durable, auto_delete=auto_delete)

    def make_queue(self, name, exchange, durable=True, auto_delete=True):
        return kombu.Queue(name, exchange, durable=durable, auto_delete=auto_delete)