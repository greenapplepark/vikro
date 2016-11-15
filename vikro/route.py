"""
vikro.route
~~~~~~~~~~~

This module provides function to parse url pattern.
"""


import re

RULE_RE = re.compile(r'''
    (?P<static>[^<]*)                           # static data
    <(?:
        (?P<type>[a-zA-Z_][a-zA-Z0-9_]*)        # type name
        ?\:)?
        (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)    # variable name
    >''', re.VERBOSE)

RE_REPLACEMENT = {
    'string': r'\w+',
    'int': r'\d+',
}

def parse_route_rule(route_rule):
    """Parse url pattern."""
    pos = 0
    end = len(route_rule)
    re_rule = r''
    while pos < end:
        match_obj = RULE_RE.match(route_rule, pos)
        if match_obj is None:
            # not found
            re_rule = '^%s$' % route_rule
            break
        match_group = match_obj.groupdict()
        re_rule += match_group['static']
        if match_group['type'] is None:
            match_group['type'] = 'string'
        if match_group['type'] not in RE_REPLACEMENT:
            raise RuntimeError('Unsupported route type: %s' % match_group['type'])
        re_rule += '(?P<%s>%s)' % (match_group['variable'], RE_REPLACEMENT[match_group['type']])
        pos = match_obj.end()
    return re.compile(re_rule)
