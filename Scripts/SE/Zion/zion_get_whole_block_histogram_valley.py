from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestBX200(TestNandRules):
    def test_bx200_get_histogram_valley(self):
        ssd = self.ssd

        arg = dut_args()
        if arg.lba is not None:
            (ch, ce, blk, page, lun) = ssd.translateLBA(arg.lba)
        else:
            ch = arg.channel
            ce = arg.ce
            lun = arg.lun
            blk = arg.block
            page = arg.page

        blk_data = self.get_one_die_histogram_valley(ch, ce, lun)

if __name__ == "__main__":
    def extended_arguments(parser):
        parser.add_argument('-ce', '--ce', type = int, default = 0)
        parser.add_argument('-ch', '--channel', type = int, default = 0)
        parser.add_argument('-lun', '--lun', type = int, default = 0)
        parser.add_argument('-b', '--block', type = int, default = 0)
        parser.add_argument('-p', '--page', type = int, default = 0)
        parser.add_argument('-lba', '--lba', type = int, default = None)

    dut_run_pyunit_test(extended_arguments = extended_arguments)
