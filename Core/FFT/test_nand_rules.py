import dm3
import time
import struct
import unittest
from Fixture.fixture import *
from Util.decorator import method_tracer
from Util.mixin import *

class TestNandRules(unittest.TestCase):
    def setUp(self):
        print
        print '*********************************************************'
        print 'Set up starts'
        print '*********************************************************'
        # FIXME add wait to wait for power on delay from last case
        print 'sleep 5'
        # time.sleep(5)

        ssd = self.ssd = dut_setup_ssd(self)

        test_nand_rules_mixin_module_name = 'test_%s_nand_rules_mixin' % ssd['abbreviation'].lower()
        exec('import %s' % test_nand_rules_mixin_module_name)
        exec('mixin(self, %s.Test%sNandRules)' % (test_nand_rules_mixin_module_name, ssd.product_familiy_id()))

        self.set_up()

        print
        print '*********************************************************'
        print 'Workload starts'
        print '*********************************************************'

    def tearDown(self):
        print
        print '*********************************************************'
        print 'Tear down starts'
        print '*********************************************************'

        ssd = self.ssd

        try:
            self.tear_down()
        finally:
            dut_teardown_device(ssd)

    @method_tracer()
    def secure_erase(self):
        ssd = self.ssd
        buf = dm3.Buffer(1)
        buf.FillZeros()
        password = "UserPassword"
        buf.SetString(2, password)
        with dm3.DeviceContext(ssd, commandTimeOut = 60):
            ssd.security().SetPassword(buf)
            ssd.security().ErasePrepare()
            ssd.security().EraseUnit(buf)

    @method_tracer()
    def write_one_sector_of_data(self, lba, data):
        ssd = self.ssd

        if isinstance(data, int):
            buf = dm3.Buffer(1)
            buf.Fill(data)
        else:
            ssd.assert_true(isinstance(data, dm3.Buffer))
            buf = data

        ssd.WriteDmaExt(lba, 1, buf)

        return self

    @method_tracer()
    def read_verify_one_sector_of_data(self, lba, data):
        ssd = self.ssd

        if isinstance(data, int):
            buf = dm3.Buffer(1)
            buf.Fill(data)
        else:
            ssd.assert_true(isinstance(data, dm3.Buffer))
            buf = data

        rBuffer = dm3.Buffer(1)
        ssd.ReadDmaExt(lba, 1, rBuffer)

        rBuffer.CompareTo(buf, 0, 1)

        return self

    @method_tracer()
    def write_full_pack_of_data(self):
        return self.write_fi_aligned(0, self._align(self.ssd.max_lba(), self.ssd['max_sectors_per_read_write']))

    @method_tracer(name_only = True)
    def write_fi_aligned(self, start_lba, end_lba, data = 0xA5, sectors_per_write = None):
        ssd = self.ssd

        self.assertTrue(start_lba % ssd['sectors_per_fi_chunk'] == 0 and (end_lba - start_lba) % ssd['sectors_per_fi_chunk'] == 0)

        # Find max divider
        if sectors_per_write is None:
            sectors_per_write = self._calc_max_sectors_per_read_write(start_lba, end_lba)

        self.assertTrue(sectors_per_write % ssd['sectors_per_fi_chunk'] == 0)
        self.assertTrue((end_lba - start_lba) % sectors_per_write == 0)

        wBuffer = dm3.Buffer(sectors_per_write)
        wBuffer.Fill(data)
        for lba in xrange(start_lba, end_lba, sectors_per_write):
            ssd.WriteDmaExt(lba, sectors_per_write, wBuffer)

        return self

    @method_tracer()
    def read_full_pack_of_data(self):
        return self.read_fi_aligned(0, self._align(self.ssd.max_lba(), self.ssd['max_sectors_per_read_write']))

    @method_tracer(name_only = True)
    def read_fi_aligned(self, start_lba, end_lba, data = 0xA5, sectors_per_read = None, verify = False):
        ssd = self.ssd

        # Find max divider
        if sectors_per_read is None:
            sectors_per_read = self._calc_max_sectors_per_read_write(start_lba, end_lba)

        self.assertTrue((end_lba - start_lba) % sectors_per_read == 0)

        uncorrectable_reads = []

        wBuffer = dm3.Buffer(sectors_per_read)
        wBuffer.Fill(data)
        rBuffer = dm3.Buffer(sectors_per_read)
        rBuffer.Fill(0x00)

        for lba in xrange(start_lba, end_lba, sectors_per_read):
            try:
                ssd.ReadDmaExt(lba, sectors_per_read, rBuffer)
            except:
                uncorrectable_reads.append((lba, sectors_per_read))
            else:
                if verify:
                    self.assertTrue(rBuffer.CompareTo(wBuffer, 0, sectors_per_read).AreEqual)

        return uncorrectable_reads

    def _align(self, data, align):
        return data - data % align

    def _calc_max_sectors_per_read_write(self, start_lba, end_lba):
        ssd = self.ssd

        sectors_per_read_write = ssd['max_sectors_per_read_write']
        while (end_lba - start_lba) % sectors_per_read_write != 0:
            sectors_per_read_write -= ssd['sectors_per_fi_chunk']

        print 'sectors_per_read_write', sectors_per_read_write
        return sectors_per_read_write

