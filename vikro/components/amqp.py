"""
vikro.components.amqp
~~~~~~~~~~~~~~~~~~~~~

This module provides amqp support for vikro, using haigha.
"""

import uuid
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
    def __init__(self, service_name, server_address, server_port, username, password):
        super(AMQPComponent, self).__init__()
        self._service_name = service_name
        self._component_type = COMPONENT_TYPE_AMQP
        self._address = server_address
        self._port = int(server_port)
        self._username = username
        self._password = password
        # using mac address as response ID
        self._response_id = str(uuid.getnode())

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
        self._main_callback = None
        self._should_keep_connect = False
        self._next_retry = 2

    def initialize(self):
        self._should_keep_connect = True
        try:
            self._initialize()
        except Exception, ex:
            logger.warning(
                '[initialize] Failed to connect to AMQP server %s:%s, %s.',
                self._address,
                self._port, ex)
        gevent.spawn(self._keep_connecting)
        gevent.spawn(self._pump)

    def _initialize(self):
        """Do actural initialize job."""
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

    def _keep_connecting(self):
        """A greenlet try to keep amqp connections."""
        while self._should_keep_connect:
            try:
                if not self._connection.closed:
                    logger.debug(
                        '[_keep_connecting] Connected to %s:%s!',
                        self._address,
                        self._port)
                    gevent.sleep(10)
                else:
                    if not self._should_keep_connect:
                        break
                    try:
                        logger.debug(
                            '[_keep_connecting] Try to reconnect to %s:%s.',
                            self._address,
                            self._port)
                        self._initialize()
                        self._next_retry = 2
                    except KeyboardInterrupt:
                        break
                    except Exception:
                        gevent.sleep(self._next_retry)
                        self._next_retry = min(self._next_retry * 2, 120)
                    finally:
                        # self._close_connections()
                        pass
            except KeyboardInterrupt:
                break

    def finalize(self):
        self._should_keep_connect = False
        self._close_connections()

    def _close_connections(self):
        """Close channels and connections."""
        if self._rpc_server_channel:
            self._rpc_server_channel.close()
            self._rpc_server_channel = None
        if self._rpc_response_channel:
            self._rpc_response_channel.close()
            self._rpc_response_channel = None
        if self._rpc_request_channel:
            self._rpc_request_channel.close()
            self._rpc_request_channel = None
        if self._connection:
            self._connection.close()
            self._connection = None

    def set_main_callback(self, callback):
        """Set main callback for amqp component."""
        self._main_callback = callback

    def _pump(self):
        """Listen to the main queue of the service.
        Other service may send rpc request to this queue.
        """
        while self._should_keep_connect:
            if self._main_callback is None:
                gevent.sleep(10)
            else:
                try:
                    logger.debug('[_pump] Try to setup consume queues.')
                    self._rpc_server_channel.basic.consume(
                        queue=self._server_queue_name,
                        consumer=self._main_callback,
                        no_ack=True)
                    self._rpc_response_channel.basic.consume(
                        queue=self._response_queue_name,
                        consumer=self._handle_rpc_response,
                        no_ack=True)
                except Exception, ex:
                    logger.error(ex)
                    gevent.sleep(self._next_retry)
                    continue
                # always try to listen
                while self._should_keep_connect and not self._connection.closed:
                    try:
                        # Pump
                        self._connection.read_frames()
                        # Yield to other greenlets so they don't starve
                        gevent.sleep()
                    except KeyboardInterrupt:
                        break
                    except Exception, ex:
                        logger.error(ex)
                    finally:
                        pass

    def _handle_rpc_response(self, message):
        """Handle rpc response and send response back to requester."""
        logger.debug('[_handle_rpc_response] Got rpc message: %s.', message)
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
        return not self._connection.closed
