"""
vikro.components.amqp
~~~~~~~~~~~~~~~~~~~~~

This module provides amqp support for vikro, using haigha.
"""

import logging
import gevent
import haigha.connection
from vikro.components import BaseComponent, COMPONENT_TYPE_AMQP
from vikro.util import id_generator

logger = logging.getLogger(__name__)

class AMQPComponent(BaseComponent):
    """AMQPComponent provides functionality to listen and publish messages
    to amqp broker and also it has method try to keep connect to broker if
    it's disconnected.
    """
    def __init__(self, service_name, server_address, server_port, username, password):
        super(AMQPComponent, self).__init__()
        self._service_name = service_name
        self._component_type = COMPONENT_TYPE_AMQP
        self._address = server_address
        self._port = int(server_port)
        self._username = username
        self._password = password
        self._response_id = id_generator()

        self._connection = None
        self._rpc_server_channel = None
        self._rpc_response_channel = None
        self._rpc_request_channel = None

        self._exchange_name = 'service_{0}_exchange'.format(self._service_name)
        self._server_queue_name = 'service_{0}_queue_server'.format(self._service_name)
        self._response_queue_name = 'service_{0}_queue_{1}'.format(
            self._service_name,
            self._response_id)

        self._rpc_callback_dict = {}
        self._should_keep_connect = False

    def initialize(self):
        self._should_keep_connect = True
        self._connection = haigha.connection.Connection(
            transport='gevent',
            host=self._address,
            port=self._port,
            user=self._username,
            password=self._password
        )
        self._rpc_server_channel = self._connection.channel()
        self._rpc_response_channel = self._connection.channel()
        self._rpc_request_channel = self._connection.channel()

        self._rpc_server_channel.exchange.declare(
            self._exchange_name,
            'direct',
            durable=True,
            nowait=False)
        # rpc server queue
        self._rpc_server_channel.queue.declare(
            self._server_queue_name,
            durable=True,
            auto_delete=True,
            nowait=False)
        self._rpc_server_channel.queue.bind(
            self._server_queue_name,
            self._exchange_name,
            'server',
            nowait=False)
        # rpc response queue
        self._rpc_response_channel.queue.declare(
            self._response_queue_name,
            durable=True,
            auto_delete=True,
            nowait=False)
        self._rpc_response_channel.queue.bind(
            self._response_queue_name,
            self._exchange_name,
            self._response_id,
            nowait=False)

    def finalize(self):
        self._should_keep_connect = False
        self._rpc_server_channel.close()
        self._rpc_response_channel.close()
        self._rpc_request_channel.close()
        self._connection.close()

    def listen_to_queue(self, callback):
        """Listen to the main queue of the service.
        Other service may send rpc request to shi queue.
        """
        self._rpc_server_channel.basic.consume(
            queue=self._server_queue_name,
            consumer=callback,
            no_ack=True)
        self._rpc_response_channel.basic.consume(
            queue=self._response_queue_name,
            consumer=self._handle_rpc_response,
            no_ack=True)
        # always try to listen
        while self._should_keep_connect:
            try:
                while self._connection is not None:
                    # Pump
                    self._connection.read_frames()
                    # Yield to other greenlets so they don't starve
                    gevent.sleep()
            except Exception, ex:
                logger.error(ex)
            finally:
                pass

    def _handle_rpc_response(self, message):
        """Handle rpc response and send response back to requester."""
        logger.debug('[_handle_rpc_response] got rpc message: %s', message)
        if ('correlation_id' in message.properties
                and message.properties['correlation_id'] in self._rpc_callback_dict):
            self._rpc_callback_dict[message.properties['correlation_id']](message)

    def register_rpc_callback(self, reply_key, callback):
        """Register rpc call to dict."""
        self._rpc_callback_dict[reply_key] = callback

    def remove_rpc_callback(self, reply_key):
        """Unregister rpc call."""
        del self._rpc_callback_dict[reply_key]

    def send_request(self, payload, exchange_name):
        """Send RPC request to dest service."""
        self._rpc_request_channel.basic.publish(payload, exchange_name, 'server')

    def send_response(self, payload, exchange_name, routing_key):
        """Send response back to requester."""
        self._rpc_response_channel.basic.publish(payload, exchange_name, routing_key)

    @property
    def component_type(self):
        return self._component_type

    @property
    def response_id(self):
        """Get RPC server response ID."""
        return self._response_id

    @property
    def exchange_name(self):
        """Get RPC server exchange name."""
        return self._exchange_name

    def is_connected(self):
        """Check if we connect to amqp."""
        return self._connection != None
