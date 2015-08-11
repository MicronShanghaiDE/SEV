from Util.assertion import Assertion
from Util.decorator import *

class Security(Assertion):
    def __init__(self, ssd):
        self.ssd = ssd
        self.security = self.ssd.device.Security

