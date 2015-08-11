from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestBx200StaticTrim(TestNandRules):
    def test_bx200_static_trim(self):
        ssd = self.ssd

        self.nandSetInterfaceMode('sdr', freq = 35)
        """
        for ch in xrange(0, ssd['max_ch']):
            for ce in xrange(0, ssd['max_ce']):
                for lun in xrange(0, ssd['max_lun']):
                    self.static_trim_write(ch, ce, lun, 0x15, 0x50)
                    self.static_trim_write(ch, ce, lun, 0x16, 0x50)
        
        for ch in xrange(0, ssd['max_ch']):
            for ce in xrange(0, ssd['max_ce']):
                for lun in xrange(0, ssd['max_lun']):
                    self.read_trim_register(ch, ce, lun, 0x12, 0x1a)
                    #self.assertEqual(self.static_trim_read(ch, ce, lun, 0x0c), 0x04)
                    # self.assertEqual(self.static_trim_read(ch, ce, lun, 0x16), 0x50)
        """
        self.read_trim_register(0, 0, 0, 0, 0x1a)
        self.read_trim_register(0, 0, 0, 0, 0x1b)

        self.nandSetInterfaceMode('ddr', freq = 100)

if __name__ == "__main__":
    dut_run_pyunit_test()
