"""
vikro.util
~~~~~~~~~~

This module provides some utility functions.
"""

import string
import random
import ConfigParser
import logging.config

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
})


def id_generator(size=6, chars=string.ascii_letters + string.digits):
    """Generate random string."""
    return ''.join(random.choice(chars) for _ in range(size))


class Config2Dict(ConfigParser.ConfigParser):
    """Convert configuration to a dict."""

    def as_dict(self):
        """Config to dict."""
        config_dict = dict(self._sections)
        for k in config_dict:
            config_dict[k] = dict(self._defaults, **config_dict[k])
            config_dict[k].pop('__name__', None)
        return config_dict
