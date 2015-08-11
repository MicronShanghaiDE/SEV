from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestBx200StaticTrim(TestNandRules):
    def test_bx200_static_trim(self):
        ssd = self.ssd
        self.channel = 0
        self.chip_enable = 0

        arg = dut_args()
        ch = arg.channel
        ce = arg.ce
        lun = arg.lun
        addr = arg.addr

        self.nandSetInterfaceMode('sdr', freq = 35)

        self.static_trim_read(0, 0, 0, 0x15)
        self.static_trim_read(0, 0, 1, 0x15)
        self.static_trim_write(0, 0, 0, 0x15, 0x50)
        self.static_trim_write(0, 0, 1, 0x15, 0x50)
        self.static_trim_read(0, 0, 0, 0x15)
        self.static_trim_read(0, 0, 1, 0x15)

        self.nandSetInterfaceMode('ddr', freq = 100)
        # ssd.exec_WriteDma(0, 1)

if __name__ == "__main__":
    def extended_arguments(parser):
        parser.add_argument('-ce', '--ce', type = int, default = 0)
        parser.add_argument('-ch', '--channel', type = int, default = 0)
        parser.add_argument('-lun', '--lun', type = int, default = 0)
        parser.add_argument('-addr', '--addr', type = int, default = 0)

    dut_run_pyunit_test(extended_arguments = extended_arguments)
