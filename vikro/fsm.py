"""
vikro.fsm
~~~~~~~~~

This module implements finite state machine of BaseService.
"""

from functools import partial
from gevent.event import Event

class StateMachine(object):
    """This finite state machine class can read configuration from dict.
    {
        'initial': 'init',
        'transitions':
        [
            {'name': 'start', 'src': 'init', 'dst': 'starting'},
            {'name': 'started', 'src': 'starting', 'dst': 'running'},
            {'name': 'stop', 'src': 'running', 'dst': 'stopping'},
            {'name': 'stopped', 'src': 'stopping', 'dst': 'init'},
        ]
    }
    In example above, the state machine is started in 'init' state.
    In transitions part, calling 'name' will change state from 'src' to 'dst'.
    """
    def __init__(self, config):
        try:
            self._initial = config['initial']
            self._transitions = config['transitions']
        except KeyError:
            raise RuntimeError('Invalid StateMachine config')
        self._current_state = self._initial
        self._wait_events = {}
        self._parse_transitions(self._transitions)

    def _parse_transitions(self, transitions):
        """Parse dict configuration and generate methods."""
        for transition in transitions:
            if (transition['src'] != self._initial
                    and transition['src'] not in self._wait_events):
                self._wait_events[transition['src']] = Event()
                self._wait_events[transition['src']].set()
            if (transition['dst'] != self._initial
                    and transition['dst'] not in self._wait_events):
                self._wait_events[transition['dst']] = Event()
                self._wait_events[transition['dst']].set()
            setattr(
                self, transition['name'],
                partial(self.change_state, transition['src'], transition['dst']))

    @property
    def current_state(self):
        """Get current state."""
        return self._current_state

    def change_state(self, from_state, to_state):
        """Change state."""
        if from_state != self._current_state:
            raise RuntimeError(
                'Change state from {} to {} is not valid.'.format(self._current_state, to_state))
        if from_state != self._initial:
            self._wait_events[from_state].set()
        self._current_state = to_state
        if to_state != self._initial:
            self._wait_events[to_state].clear()

    def wait_in(self, wait_in_state):
        """State will wait until be transited."""
        if wait_in_state in self._wait_events:
            self._wait_events[wait_in_state].wait()
