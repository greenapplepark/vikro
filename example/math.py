"""
MathService example.
"""

from vikro.service import BaseService, route

class MathService(BaseService):
    """Math service."""

    @route('/add/<int:addend1>/<int:addend2>')
    def add(self, addend1, addend2):
        return addend1 + addend2

    @route('/subtract/<int:minuend>/<int:subtrahend>')
    def subtract(self, minuend, subtrahend):
        return minuend - subtrahend

    @route('/multiply/<int:multiplier1>/<int:multiplier2>')
    def multiply(self, multiplier1, multiplier2):
        return multiplier1 * multiplier2

    @route('/divide/<int:dividend>/<int:divisor>')
    def divide(self, dividend, divisor):
        return dividend / divisor
