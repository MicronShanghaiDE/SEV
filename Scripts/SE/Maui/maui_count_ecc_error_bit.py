from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestMaui(TestNandRules):
    def test_maui_ecc_error_bit(self):
        ssd = self.ssd

        ecc_error_bit = {}
        for ch in xrange(ssd['max_ch']):
            for ce in xrange(ssd['max_ce']):
                for blk in xrange(4096):
                    for page in xrange(128):
                        name = "%d_%d_%d_%d" % (ch, ce, blk, page)
                        ecc_error_bit[name] = {}

        for lba in xrange(0, ssd.max_lba(), 2):
            error_bit = self.vu_1kb_read_to_report_ecc(lba)
            if (error_bit != 0) and (error_bit != 255):
                (ch, ce, blk, page, lun, sector) = self.translate_lba(lba)
                name = "%d_%d_%d_%d" % (ch, ce, blk, page)
                ecc_error_bit[name][sector] = error_bit
        '''
        zero_buf = dm3.Buffer(1)
        zero_buf.FillZeros()
        # for offset in xrange(0, ssd.max_lba() - 512, 512):
        for offset in xrange(0, 1000000, 512):
            offset = offset / 512
            err_buf = self.check_all_lba_ecc_error_count(offset)
            offset = offset * 512
            if not err_buf.CompareTo(zero_buf, 0, 1).AreEqual:
                for i in xrange(0, 512, 2):
                    if (err_buf.GetByte(i) != 0) and (err_buf.GetByte(i) != 255):
                        (ch, ce, blk, page, lun, sector) = self.translate_lba(offset + i)
                        name = "%d_%d_%d_%d" % (ch, ce, blk, page)
                        ecc_error_bit[name][sector] = err_buf.GetByte(i)
        '''
        log_name = "SN%s.log" % ssd.IdentifyDevice().SerialNumber
        saveout = sys.stdout
        fsock = open(log_name, 'w')
        sys.stdout = fsock
        for ch in xrange(ssd['max_ch']):
            for ce in xrange(ssd['max_ce']):
                for blk in xrange(4096):
                    for page in xrange(128):
                        name = "%d_%d_%d_%d" % (ch, ce, blk, page)
                        if len(ecc_error_bit[name].keys()) != 0:
                            for sector in ecc_error_bit[name].keys():
                                print "CH: %d, CE: %d, BLK: %d, Page: %d, Sector: %d, Error_bit: %d" % (ch, ce, blk, page, sector, ecc_error_bit[name][sector])
        sys.stdout = saveout
        fsock.close()

if __name__ == "__main__":
    dut_run_pyunit_test()
