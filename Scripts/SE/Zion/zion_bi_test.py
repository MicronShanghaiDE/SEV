from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestBx200BI(TestNandRules):
    def test_bx200_burnin(self):
        ssd = self.ssd
        self.bist_execution()

if __name__ == "__main__":
    dut_run_pyunit_test()
