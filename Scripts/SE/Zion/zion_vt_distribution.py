from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestBX200(TestNandRules):
    def test_bx200_vt_distribution(self):
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

        print "Program the page using direct nand command"
        byte_size = 27888
        sector = (int(byte_size) + 511) / 512
        buf = dm3.Buffer(sector)
        buf.FillRandom()
        """
        res = self.erase_direct(ch, ce, lun, blk, page)
        # ssd.tlc_program(ch, ce, lun, blk, page, buf, byte_size, 0x43)
        self.tlc_program(ch, ce, lun, blk, page, buf, byte_size, 0x41)
        # ssd.tlc_program(ch, ce, lun, blk, page + 1, buf, byte_size, 0x41)
        # ssd.tlc_program(ch, ce, lun, blk, page + 2, buf, byte_size, 0x41)
        # ssd.tlc_program(ch, ce, lun, blk, page + 3, buf, byte_size, 0x41)
        # ssd.tlc_program(ch, ce, lun, blk, page + 4, buf, byte_size, 0x41)
        # ssd.tlc_program(ch, ce, lun, blk, page + 5, buf, byte_size, 0x41)
        buf1 = self.hmlcx7_histogram_read(ch, ce, lun, blk, page)
        dic1 = self.count_vt(buf1, ssd['histo_length'])
        # ssd.tlc_program(ch, ce, lun, blk, page + 1, buf, byte_size, 0x43)
        res = self.erase_direct(ch, ce, lun, blk, page)
        self.tlc_program(ch, ce, lun, blk, page, buf, byte_size, 0x42)
        # ssd.tlc_program(ch, ce, lun, blk, page + 1, buf, byte_size, 0x42)
        # ssd.tlc_program(ch, ce, lun, blk, page + 2, buf, byte_size, 0x42)
        # ssd.tlc_program(ch, ce, lun, blk, page + 3, buf, byte_size, 0x42)
        buf2 = self.hmlcx7_histogram_read(ch, ce, lun, blk, page)
        dic2 = self.count_vt(buf2, ssd['histo_length'])
        # ssd.tlc_program(ch, ce, lun, blk, page + 2, buf, byte_size, 0x43)
        res = self.erase_direct(ch, ce, lun, blk, page)
        self.tlc_program(ch, ce, lun, blk, page, buf, byte_size, 0x43)
        """
        self.tlc_program(ch, ce, lun, blk, page + 1, buf, byte_size, 0x43)

        buf3 = self.hmlcx7_histogram_read(ch, ce, lun, blk, page + 1)
        dic3 = self.count_vt(buf3, ssd['histo_length'])

        self.draw_plot(plot3 = dic3)

if __name__ == "__main__":
    def extended_arguments(parser):
        parser.add_argument('-ce', '--ce', type = int, default = 0)
        parser.add_argument('-ch', '--channel', type = int, default = 0)
        parser.add_argument('-lun', '--lun', type = int, default = 0)
        parser.add_argument('-b', '--block', type = int, default = 0)
        parser.add_argument('-p', '--page', type = int, default = 0)
        parser.add_argument('-lba', '--lba', type = int, default = None)
        parser.add_argument('-wb', '--whole_block', type = int, default = None)

    dut_run_pyunit_test(extended_arguments = extended_arguments)
