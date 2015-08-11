from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestBx200Smart(TestNandRules):
    def test_bx200_smart(self):
        ssd = self.ssd
        buf = dm3.Buffer(1)
        ssd.smart().ReadData(buf)
        print buf

if __name__ == "__main__":
    dut_run_pyunit_test()
