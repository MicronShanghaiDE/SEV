from Util.assertion import Assertion
from Util.decorator import *

class HbaPort(Assertion):
    def __init__(self, ssd):
        self.ssd = ssd
        self.hbaport = self.ssd.device.HbaPort

