class AMQPRequest(object):

    def __init__(self, func_name, func_args, func_kwargs, reply_to, reply_key):
        self.func_name = func_name
        self.func_args = func_args
        self.func_kwargs = func_kwargs
        self.reply_to = reply_to
        self.reply_key = reply_key

    def __str__(self):
        return ('AMQPRequest(func_name={}, func_args={}, func_kwargs={}, reply_to={}, reply_key={})'
                .format(self.func_name, self.func_args, self.func_kwargs, self.reply_to, self.reply_key))


class AMQPResponse(object):

    def __init__(self, result):
        self.result = result

    def __str__(self):
        return "AMQPResponse(result={})".format(self.result)

    @property
    def is_exception(self):
        return isinstance(self.result, BaseException)