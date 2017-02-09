"""
vikro.models
~~~~~~~~~~~~

This module contains the AMQPRequest and AMQPResponse class.
These class are used in AMQP RPC.
"""

try:
    import simplejson as json
except ImportError:
    import json


class AMQPRequest(object):
    """The request object send to AMQP broker.
    :param func_name: rpc function name.
    :param func_args: rpc function args.
    :param func_kwargs: rpc function kwargs.
    :param reply_to: reply exchange name.
    :param response_id: reply queue bind id (A service could have more than one reply queue).
    :param reply_key: it is used to distinguish different request.
    """

    def __init__(self, func_name, func_args, func_kwargs, reply_to, response_id, reply_key):
        self.func_name = func_name
        self.func_args = func_args
        self.func_kwargs = func_kwargs
        self.reply_to = reply_to
        self.response_id = response_id
        self.reply_key = reply_key

    def __str__(self):
        return (
            ('AMQPRequest(func_name={0},func_args={1}, '
             'func_kwargs={2}, reply_to={3}, response_id={4}, reply_key={5})').format(
                 self.func_name,
                 self.func_args,
                 self.func_kwargs,
                 self.reply_to,
                 self.response_id,
                 self.reply_key))

    def to_json(self):
        """Serialize AMQPRequest object to json."""
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_raw):
        """Create AMQPRequest object from json."""
        _dict = json.loads(str(json_raw))
        return AMQPRequest(
            _dict['func_name'],
            _dict['func_args'],
            _dict['func_kwargs'],
            _dict['reply_to'],
            _dict['response_id'],
            _dict['reply_key'])

class AMQPResponse(object):
    """The response object received from AMQP broker.
    It could be an exception.
    """

    def __init__(self, result):
        self.result = result
        self.is_exception = isinstance(self.result, BaseException)

    def __str__(self):
        return 'AMQPResponse(result={0})'.format(self.result)

    def to_json(self):
        """Serialize AMQPResponse object to json."""
        if not self.is_exception:
            return json.dumps(self.__dict__)
        else:
            type_exception = type(self.result)
            _dict = {
                'is_exception': True,
                'result': {
                    'exception_module': type_exception.__module__,
                    'exception_name': type_exception.__name__,
                    'exception_message': self.result.message
                }
            }
            return json.dumps(_dict)

    @staticmethod
    def from_json(json_raw):
        """Create AMQPResponse object from json."""
        _dict = json.loads(str(json_raw))
        obj = AMQPResponse(_dict['result'])
        obj.is_exception = _dict['is_exception']
        return obj
