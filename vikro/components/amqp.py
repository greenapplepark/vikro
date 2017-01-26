"""
vikro.components.amqp
~~~~~~~~~~~~~~~~~~~~~

This module provides amqp support for vikro, using haigha.
"""

import logging
import gevent
import haigha.connection
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
        self._connection = haigha.connection.Connection(
            transport='gevent',
            host=server_address,
            port=int(server_port),
            user=username,
            password=password
        )
        self._channel = self._connection.channel()
        self._should_keep_connect = False
        self._next_retry = 2

    def initialize(self):
        self._should_keep_connect = True
        # self._should_keep_connect = True
        # try:
        #     self._connection.connect()
        # except Exception, ex:
        #     logger.warning('Failed to connect to AMQP server %s, %s.', self._url, ex)
        # gevent.spawn(self.keep_connecting)

    def finalize(self):
        self._should_keep_connect = False
        self._connection.close()

    def get_connection(self):
        """Get amqp connection."""
        return self._connection

    def get_channel(self):
        return self._channel

    # def keep_connecting(self):
    #     """A greenlet try to keep amqp connections."""
    #     while self._should_keep_connect:
    #         try:
    #             if self._connection.connected:
    #                 logger.debug('Connected to %s!', self._url)
    #                 gevent.sleep(10)
    #             else:
    #                 if not self._should_keep_connect:
    #                     break
    #                 try:
    #                     logger.debug('Try to reconnect to %s.', self._url)
    #                     self._connection.connect()
    #                     self._next_retry = 2
    #                 except Exception:
    #                     gevent.sleep(self._next_retry)
    #                     self._next_retry = min(self._next_retry * 2, 120)
    #         except KeyboardInterrupt:
    #             break

    def listen_to_queue(self, service_name, queue_name, callback):
        """Listen to the main queue of the service.
        Other service may send rpc request to shi queue.
        """
        exchange_name = 'service_{0}_exchange'.format(service_name)
        self.make_exchange(exchange_name)
        self.make_queue(queue_name, exchange_name)
        self._channel.basic.consume(
            queue=queue_name,
            consumer=callback,
            no_ack=True)
        # always try to listen
        while self._should_keep_connect:
            try:
                while self._connection is not None:
                    # Pump
                    self._connection.read_frames()
                    # Yield to other greenlets so they don't starve
                    gevent.sleep()
            finally:
                pass
            # while self.is_connected() is False:
            #     logger.info('Waiting for connection...')
            #     gevent.sleep(3)
            # conn = self.get_connection()
            # with conn.Consumer(queues=queue, callbacks=[callback], accept=['pickle']):
            #     while self._should_keep_connect:
            #         try:
            #             conn.drain_events(timeout=0.01)
            #         except socket.timeout:
            #             pass
            #         except KeyboardInterrupt:
            #             return
            #         except Exception, ex:
            #             logger.error(ex)
            #             break
            #         gevent.sleep(0.01)

    def publish_message(self, payload, exchange_name, routing_key='default'):
        """Publish message to specific exchange using routing_key."""
        self._channel.basic.publish(payload, exchange_name, routing_key)
        # conn = self.get_connection()
        # exchange = self.make_exchange(exchange_name)
        # with producers[conn].acquire(block=True) as producer:
        #     producer.publish(
        #         payload,
        #         exchange=exchange,
        #         serializer='pickle',
        #         routing_key=routing_key)

    @property
    def component_type(self):
        return self._component_type

    def is_connected(self):
        """Check if we connect to amqp."""
        return self._connection != None

    def make_exchange(self, name, ex_type='direct', durable=True):
        """Make a exchange."""
        self._channel.exchange.declare(
            name,
            ex_type,
            durable=durable)
        # return self._channel.exchange.declare(
        #     name,
        #     ex_type,
        #     durable=durable,
        #     auto_delete=auto_delete,
        #     channel=self._connection)

    def make_queue(self, name, exchange_name, routing_key='default', durable=True, auto_delete=True):
        """Make a queue."""
        self._channel.queue.declare(
            name,
            durable=durable,
            auto_delete=auto_delete)
        self._channel.queue.bind(name, exchange_name, routing_key)
        # ret_queue = kombu.Queue(
        #     name,
        #     exchange,
        #     routing_key=routing_key,
        #     durable=durable,
        #     auto_delete=auto_delete,
        #     channel=self._connection)
        # ret_queue.declare()
        # return ret_queue
