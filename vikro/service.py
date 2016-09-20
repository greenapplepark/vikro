from .fsm import StateMachine


class BaseService(object):
    
    def __init__(self, async):
        self._async = async
        self._state_machine = StateMachine(None)
        self._components = []

    def add_component(self, component):
        pass

    def start(self):
        for c in self._components:
            c.initialize()
        print "BaseService start"

    def stop(self):
        pass

    def reload(self):
        pass