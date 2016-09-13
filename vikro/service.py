from .fsm import StateMachine


class BaseService:
    
    def __init__(self):
        self._state_machine = StateMachine()
        self._components = []

    def add_component(self, component):
        pass

    def start(self):
        for c in self._components:
            c.initialize()

    def stop(self):
        pass

    def reload(self):
        pass