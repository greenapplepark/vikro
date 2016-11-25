"""
vikro.components.amqp
~~~~~~~~~~~~~~~~~~~~~

This module provides amqp support for vikro, using kombu.
"""

import socket
import logging
import gevent
import kombu
from kombu.pools import producers
from vikro.components import BaseComponent, COMPONENT_TYPE_AMQP

logger = logging.getLogger(__name__)

class AMQPComponent(BaseComponent):
    """AMQPComponent provides functionality to listen and publish messages
    to amqp broker and also it has method try to keep connect to broker if
    it's disconnected.
    """
    def __init__(self, server_address, server_port, username, password):
        super(AMQPComponent, self).__init__()
        self._component_type = COMPONENT_TYPE_AMQP
        self._url = 'amqp://{0}:{1}@{2}:{3}/'.format(
            username,
            password,
            server_address,
            server_port)
        self._connection = kombu.Connection(self._url)
        self._should_keep_connect = False
        self._next_retry = 2

    def initialize(self):
        self._should_keep_connect = True
        try:
            self._connection.connect()
        except Exception, ex:
            logger.warning('Failed to connect to AMQP server %s, %s.', self._url, ex)
        gevent.spawn(self.keep_connecting)

    def finalize(self):
        self._should_keep_connect = False
        self._connection.release()

    def get_connection(self):
        """Get amqp connection."""
        return self._connection

    def keep_connecting(self):
        """A greenlet try to keep amqp connections."""
        while self._should_keep_connect:
            try:
                if self._connection.connected:
                    logger.debug('Connected to %s!', self._url)
                    gevent.sleep(10)
                else:
                    if not self._should_keep_connect:
                        break
                    try:
                        logger.debug('Try to reconnect to %s.', self._url)
                        self._connection.connect()
                        self._next_retry = 2
                    except Exception:
                        gevent.sleep(self._next_retry)
                        self._next_retry = min(self._next_retry * 2, 120)
            except KeyboardInterrupt:
                break

    def listen_to_queue(self, service_name, queue_name, callback):
        """Listen to the main queue of the service.
        Other service may send rpc request to shi queue.
        """
        exchange_name = 'service_{0}_exchange'.format(service_name)
        exchange = self.make_exchange(exchange_name)
        queue = self.make_queue(queue_name, exchange)
        # always try to listen
        while self._should_keep_connect:
            while self.is_connected() is False:
                logger.info('Waiting for connection...')
                gevent.sleep(3)
            conn = self.get_connection()
            with conn.Consumer(queues=queue, callbacks=[callback], accept=['pickle']):
                while self._should_keep_connect:
                    try:
                        conn.drain_events(timeout=0.01)
                    except socket.timeout:
                        pass
                    except KeyboardInterrupt:
                        return
                    except Exception, ex:
                        logger.error(ex)
                        break
                    gevent.sleep(0.01)

    def publish_message(self, payload, exchange_name, routing_key='default'):
        """Publish message to specific exchange using routing_key."""
        conn = self.get_connection()
        exchange = self.make_exchange(exchange_name)
        with producers[conn].acquire(block=True) as producer:
            producer.publish(
                payload,
                exchange=exchange,
                serializer='pickle',
                routing_key=routing_key)

    @property
    def component_type(self):
        return self._component_type

    def is_connected(self):
        """Check if we connect to amqp."""
        return self._connection.connected

    def make_exchange(self, name, ex_type='direct', durable=True, auto_delete=True):
        """Make a kombu exchange."""
        return kombu.Exchange(
            name,
            ex_type,
            durable=durable,
            auto_delete=auto_delete,
            channel=self._connection)

    def make_queue(self, name, exchange, routing_key='default', durable=True, auto_delete=True):
        """Make a kombu queue."""
        ret_queue = kombu.Queue(
            name,
            exchange,
            routing_key=routing_key,
            durable=durable,
            auto_delete=auto_delete,
            channel=self._connection)
        ret_queue.declare()
        return ret_queue
