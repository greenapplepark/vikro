class RpcRequest(object):

    def __init__(self, func_name, func_args, func_kwargs):
        self.func_name = func_name
        self.func_args = func_args
        self.func_kwargs = func_kwargs

    def __str__(self):
        return ("<RpcRequest(func_name={0}, func_args={1}, func_kwargs={2})>"
                .format(self.func_name, self.func_args, self.func_kwargs))


class RpcResponse(object):

    def __init__(self, result):
        self.result = result

    def __str__(self):
        return "<RpcResponse(result={0})>".format(self.result)

    @property
    def is_exception(self):
        return isinstance(self.result, BaseException)