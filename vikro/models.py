"""
vikro.models
~~~~~~~~~~~~

This module contains the AMQPRequest and AMQPResponse class.
These class are used in AMQP RPC.
"""

class AMQPRequest(object):
    """The request object send to AMQP broker."""
    def __init__(self, func_name, func_args, func_kwargs, reply_to, reply_key):
        self.func_name = func_name
        self.func_args = func_args
        self.func_kwargs = func_kwargs
        self.reply_to = reply_to
        self.reply_key = reply_key

    def __str__(self):
        return (
            ('AMQPRequest(func_name={0},func_args={1}, '
             'func_kwargs={2}, reply_to={3}, reply_key={4})').format(
                 self.func_name,
                 self.func_args,
                 self.func_kwargs,
                 self.reply_to,
                 self.reply_key))

class AMQPResponse(object):
    """The response object received from AMQP broker.
    It could be an exception.
    """
    def __init__(self, result):
        self.result = result

    def __str__(self):
        return 'AMQPResponse(result={0})'.format(self.result)

    @property
    def is_exception(self):
        """Check if it's an exception."""
        return isinstance(self.result, BaseException)
