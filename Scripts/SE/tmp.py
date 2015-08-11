from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestBx200StaticTrim(TestNandRules):
    def test_bx200_static_trim(self):
        ssd = self.ssd
        self.channel = 1
        self.chip_enable = 0

        # self.nandSetInterfaceMode('sdr', freq = 20)
        # self.read_status()
        # self.nandSetInterfaceMode('ddr', freq = 100)
        # self.nandSetInterfaceMode('ddr', freq = 200)

        # self.set_feature(0x01, 0x14)
        # self.get_feature(0x01)
        # self.nandSetInterfaceMode('ddr', freq = 200)
        # self.get_feature(0x01)
        # self.nandSetInterfaceMode('sdr', freq = 35)
        # self.nandSetInterfaceMode('ddr', freq = 100)
        # self.get_error_recovery_statistics(ssd['max_ch'] * ssd['max_ce'] * ssd['max_lun'])
        # self.trigger_recalibration()
        self.get_target_page_calibration_info()

        # print self.vu_1kb_read_to_report_ecc(0)
        # self.vu_1kb_read_to_report_ecc(0)
        # self.check_all_lba_ecc_error_count(0)
        # self.trigger_recalibration()
        # self.get_one_page_histogram_valley(0, 0, 0, 200, 100)

        """
        # Read Unique ID
        cmd = self.genericNandCmdModeSetup(ce, ch)
        cmd += self.genericNandCmdDirectCmd(0xED)
        cmd += self.genericNandCmdDirectAddr(0)
        cmd += self.genericPollDirectStatus()
        cmd += self.genericNandCmdDirectCmd(0x00)  # Put NAND back in read mode
        cmd += self.genericNandCmdModeEnd(True)
        buf = self.genericNandCommand(cmd, 1, 512)
        print buf
        """



    @method_tracer()
    def set_feature(self, addr, value):
        # cmd = self.genericNandCmdModeSetup(0, 1)
        cmd = self.genericNandCmdModeSetup(self.channel, self.chip_enable)
        cmd += self.genericNandCmdDirectCmd(0xEF)  # Issue Get Features
        cmd += self.genericNandCmdDirectAddr(addr)
        # cmd += self.genericPollDirectStatus()
        cmd += self.genericNandCmdDirectData(value, 4)  # Write Byte Sub Feature Param1
        cmd += self.genericNandCmdModeEnd(True)
        self.genericNandCommand(cmd)

    @method_tracer()
    def get_feature(self, addr):
        # cmd = self.genericNandCmdModeSetup(0, 1)
        cmd = self.genericNandCmdModeSetup(self.channel, self.chip_enable)
        cmd += self.genericNandCmdDirectCmd(0xEE)  # Issue Get Features
        cmd += self.genericNandCmdDirectAddr(addr)
        cmd += self.genericPollDirectStatus()
        cmd += self.genericNandCmdDirectCmd(0x00)  # Put NAND back in read mode
        cmd += self.genericNandCmdModeEnd(True)
        buf = self.genericNandCommand(cmd, 1, 4)
        return "0x%x" % buf.GetByte(0)

    def read_status(self):
        cmd = self.genericNandCmdModeSetup(self.channel, self.chip_enable)
        cmd += self.genericPollDirectStatus()
        cmd += self.genericNandCmdModeEnd(True)
        buf = self.genericNandCommand(cmd, 1, 1)
        print buf


if __name__ == "__main__":
    dut_run_pyunit_test()
