from Fixture.fixture import *
from FFT.test_nand_rules import *
from Util.decorator import method_tracer

class TestMaui(TestNandRules):
    @method_tracer()
    def _read_stress(self):
        ssd = self.ssd
        print "Read stress test"
        print "Random 4KB read"
        start_time = time.clock()
        end_time = time.clock()
        end_lba = self._align(self.ssd.max_lba(), self.ssd['max_sectors_per_read_write'])
        while ((end_time - start_time) < 1):  # 6.5hrs
            # random 4k read
            for i in xrange(1000):
                lba = random.randint(0, end_lba - 8)
                ssd.ReadDmaExt(lba, 8)
            end_time = time.clock()

        print "Random 8KB read"
        start_time = time.clock()
        end_time = time.clock()
        while ((end_time - start_time) < 1):  # 6.5hrs
            # random 8k read
            for i in xrange(1000):
                lba = random.randint(0, end_lba - 16)
                ssd.ReadDmaExt(lba, 16)
            end_time = time.clock()

        print "Continuous read of same 1.8MB region"
        lba_fixed = random.randint(0, end_lba - 3840)
        start_time = time.clock()
        end_time = time.clock()
        while ((end_time - start_time) < 1):  # 13hrs
            # continuous read of same 1.8MB region
            for lba in xrange(lba_fixed, lba_fixed + 3840, 256):
                ssd.ReadDmaExt(lba, 256)
            end_time = time.clock()

    def test_maui_rdt_flow(self):
        ssd = self.ssd
        self.write_full_pack_of_data()
        self._read_stress()

        ssd.StandbyImmediate()
        ssd.exec_powerOff()
        ssd.wait(5)
        t0 = time.clock()
        ssd.exec_powerOn(0)

        rtf = ssd.hbaport().Rtf()
        while (rtf.Status != 0x50):
            rtf = ssd.hbaport().Rtf()
        res = ssd.ReadDmaExt(0, 8)
        print time.clock() - t0, "Seconds process time"
        print res.ExecTime / 1000000, "Seconds read execution time"

        self.read_full_pack_of_data()

if __name__ == "__main__":
    dut_run_pyunit_test()
