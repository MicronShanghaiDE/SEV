from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestBx200(TestNandRules):
    def test_bx200_get_t_pcal_info(self):
        self.get_target_page_calibration_info()

if __name__ == "__main__":
    dut_run_pyunit_test()
