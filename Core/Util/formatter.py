# Use decorator is better that allows selective trace
# instead of adding another internal function _get to handle get_xxx
import sys
import time
import cStringIO

class Formatter:
    @classmethod
    def ljust(cls, string):
        return string.ljust(60, '.')

    @classmethod
    def methodized(cls, obj, func_name, *args, **kwargs):
        return cls.ljust('%s.%s(%s) ' % (obj.__class__.__name__,
                                         func_name,
                                         ', '.join(map(str, args) + map(lambda item: str(item[0]) + ' = ' + repr(item[1]), kwargs.items()))))
    @classmethod
    def tablized(self, text):
        '''Add tab at beginning of each line
        '''
        return ''.join(['\t' + line for line in text.splitlines(True)])
