class DutException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Assertion():
    def assert_true(self, condition, message = None):
        if not condition:
            msg = self._formatMessage(message, "%s is not true" % condition)
            raise DutException(msg)

    def assert_false(self, condition, message = None):
        if condition:
            msg = self._formatMessage(message, "%s is not false" % condition)
            raise DutException(msg)

    def assert_null(self, condition, message = None):
        if condition is not None:
            msg = self._formatMessage(message, "%s is not None" % condition)
            raise DutException(msg)

    def assert_not_null(self, condition, message = None):
        if condition is None:
            msg = self._formatMessage(message, "%s is None" % condition)
            raise DutException(msg)

    def assert_equal(self, expect, actual, message = None):
        if isinstance(expect, list) and isinstance(actual, list):
            for i in range(len(expect)):
                if expect[i] != actual[i]:
                    msg = self._formatMessage(message, '%s != %s' % (expect, actual))
                    raise DutException(msg)
        else:
            if expect != actual:
                msg = self._formatMessage(message, '%s != %s' % (expect, actual))
                raise DutException(msg)

    def assert_not_equal(self, expect, actual, message = None):
        if isinstance(expect, list) and isinstance(actual, list):
            for i in range(len(expect)):
                if expect[i] == actual[i]:
                    msg = self._formatMessage(message, '%s == %s' % (expect, actual))
                    raise DutException(msg)
        else:
            if expect == actual:
                msg = self._formatMessage(message, '%s == %s' % (expect, actual))
                raise DutException(msg)

    def assert_within(self, member, container, message = None):
        if member not in container:
            msg = self._formatMessage(message, '%s not found in %s' % (member, container))
            raise DutException(msg)

    def assert_not_within(self, member, container, message = None):
        if member in container:
            msg = self._formatMessage(message, '%s found in %s' % (member, container))
            raise DutException(msg)

    def assert_failed(self, message = None):
        msg = self._formatMessage(message, 'DUT failed')
        raise DutException(msg)

    def _formatMessage(self, msg, standardMsg):
        if msg is None:
            return standardMsg
        return msg

def assert_true(condition, message = None):
    if condition != True:
        raise DutException(message)

def assert_false(condition, message = None):
    if condition != False:
        raise DutException(message)

def assert_null(condition, message = None):
    if condition:
        raise DutException(message)

def assert_not_null(condition, message = None):
    if not condition:
        raise DutException(message)

# TODO support for list comparison
def assert_equal(expect, actual, message = None):
    if isinstance(actual, list):
        for i in actual:
            assert_equal(expect, i, message)
    else:
        assert_true(expect == actual, message)

def assert_not_equal(expect, actual, message = None):
    if isinstance(actual, list):
        for i in actual:
            assert_not_equal(expect, i, message)
    else:
        assert_true(expect != actual, message)

def assert_within(expects, actual, message = None):
    for expect in expects:
        if expect == actual:
            return
    assert_failed(message)

def assert_failed(self, message = None):
    raise DutException(message)
