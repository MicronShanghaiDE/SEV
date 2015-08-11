from Util.assertion import Assertion
from Util.decorator import *

class Smart(Assertion):
    def __init__(self, ssd):
        self.ssd = ssd
        self.smart = self.ssd.device.Smart

