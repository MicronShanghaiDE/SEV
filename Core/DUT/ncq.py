from Util.assertion import Assertion
from Util.decorator import *

class Ncq(Assertion):
    def __init__(self, ssd):
        self.ssd = ssd
        self.ncq = self.ssd.device.Ncq

