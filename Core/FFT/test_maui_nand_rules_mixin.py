import dm3
import time
from Util.decorator import method_tracer

class TestMauiNandRules:
    def set_up(self):
        ssd = self.ssd
        self.unlock()

    def tear_down(self):
        ssd = self.ssd

    @method_tracer()
    def unlock(self):
        ssd = self.ssd
        ssd.AtaCall28BitNoData(0xB3, 0, 0, 0, 0, 0, 0xFA)
        return

    @method_tracer()
    def check_all_lba_ecc_error_count(self, offset):
        ssd = self.ssd
        rBuffer = dm3.Buffer(1)
        rBuffer.FillZeros()

        ssd.AtaCall28BitReadPio(rBuffer, 512, 0xbc, 0x01, offset & 0xff, (offset >> 8) & 0xff, 0, 0, 0x21)

        return rBuffer

    @method_tracer()
    def vu_1kb_read_to_report_ecc(self, lba):
        ssd = self.ssd

        lba1 = lba & 0xff
        lba2 = (lba >> 8) & 0xff
        lba3 = (lba >> 16) & 0xff
        lba4 = (lba >> 24) & 0x0f
        drive_head = lba4 | 0x40
        rBuffer = dm3.Buffer(1)
        rBuffer.FillZeros()
        ssd.AtaCall28BitReadPio(rBuffer, 512, 0xd3, 0x01, lba1, lba2, lba3, drive_head, 0x21)

        return rBuffer.GetByte(0)

    @method_tracer()
    def translate_lba(self, lba):
        ssd = self.ssd

        # Byte Offset 0 ~ 3 Logical address (LBA)
        wBuffer = dm3.Buffer(1)
        wBuffer.FillZeros()
        wBuffer.SetByte(0, lba & 0xFF)
        wBuffer.SetByte(1, (lba >> 8) & 0xFF)
        wBuffer.SetByte(2, (lba >> 16) & 0xFF)
        wBuffer.SetByte(3, (lba >> 24) & 0xFF)

        # Logical to Physical Address Translation
        ssd.AtaCall28BitWritePio(wBuffer, 512, 0xCE, 0x01, 0, 0, 0, 0, 0x31)

        rBuffer = dm3.Buffer(1)
        rBuffer.FillZeros()
        ssd.AtaCall28BitReadPio(rBuffer, 512, 0xCF, 0x01, 0, 0, 0, 0, 0x21)

        ch = rBuffer.GetByte(0)
        ce = rBuffer.GetByte(1)
        blk = rBuffer.GetByte(2) + (rBuffer.GetByte(3) << 8)
        page = rBuffer.GetByte(4) + (rBuffer.GetByte(5) << 8)
        lun = rBuffer.GetByte(6)
        sector = rBuffer.GetByte(8)

        print "Physical address for LBA %d is ch: %d, ce: %d, lun: %d, blk: %d, page: %d" % (lba, ch, ce, lun, blk, page)

        return (ch, ce, blk, page, lun, sector)

    @method_tracer()
    def read_direct(self, ch, ce, lun, blk, page, byte_size):
        ssd = self.ssd
        row_addr = (lun << ssd['LunStartBit']) | (blk << ssd['BlockStartBit']) | (page << ssd['PageStartBit'])
        acyc3 = row_addr & 0xFF
        acyc4 = (row_addr >> 8) & 0xFF
        acyc5 = (row_addr >> 16) & 0xFF

        wBuffer = dm3.Buffer(1)
        wBuffer.SetByte(0, ce)
        wBuffer.SetByte(1, ch)
        wBuffer.SetByte(2, acyc3)
        wBuffer.SetByte(3, acyc4)
        wBuffer.SetByte(4, acyc5)

        print "Read Direct Phase 1"
        ssd.AtaCall28BitWritePio(wBuffer, 512, 0xC6, 0x01, 0, 0, 0, 0, 0x31)

        print "Read Direct Phase 2"
        sector = (byte_size + 511) / 512
        # whole page = 4320B
        rBuffer = dm3.Buffer(sector)
        rBuffer.FillZeros()
        ssd.AtaCall28BitReadPio(rBuffer, sector * 512, 0xBF, 0x09, 0, 0, 0, 0, 0x21)

        return rBuffer

    @method_tracer()
    def erase_direct(self, ch, ce, lun, blk, page = 0):
        ssd = self.ssd
        row_addr = (lun << ssd['LunStartBit']) | (blk << ssd['BlockStartBit']) | (page << ssd['PageStartBit'])
        acyc3 = row_addr & 0xFF
        acyc4 = (row_addr >> 8) & 0xFF
        acyc5 = (row_addr >> 16) & 0xFF

        wBuffer = dm3.Buffer(1)
        wBuffer.SetByte(0, ce)
        wBuffer.SetByte(1, ch)
        wBuffer.SetByte(2, acyc3)
        wBuffer.SetByte(3, acyc4)
        wBuffer.SetByte(4, acyc5)

        print "Erase Direct Phase 1"
        ssd.AtaCall28BitWritePio(wBuffer, 512, 0xC6, 0x01, 0, 0, 0, 0, 0x31)

        print "Erase Direct Phase 2"
        ssd.AtaCall28BitWritePio(wBuffer, 512, 0xC7, 0x01, 0, 0, 0, 0, 0x31)

        return

    @method_tracer()
    def write_direct(self, ch, ce, lun, blk, page, byte_size, dBuffer = None):
        ssd = self.ssd
        row_addr = (lun << ssd['LunStartBit']) | (blk << ssd['BlockStartBit']) | (page << ssd['PageStartBit'])
        acyc3 = row_addr & 0xFF
        acyc4 = (row_addr >> 8) & 0xFF
        acyc5 = (row_addr >> 16) & 0xFF

        wBuffer = dm3.Buffer(1)
        wBuffer.SetByte(0, ce)
        wBuffer.SetByte(1, ch)
        wBuffer.SetByte(2, acyc3)
        wBuffer.SetByte(3, acyc4)
        wBuffer.SetByte(4, acyc5)

        print "Write Direct Phase 1"
        ssd.AtaCall28BitWritePio(wBuffer, 512, 0xC6, 0x01, 0, 0, 0, 0, 0x31)

        # whole page = 4320B
        print "Write Direct Phase 2"
        sector = (byte_size + 511) / 512
        if dBuffer is None:
            dBuffer = dm3.Buffer(sector)
            dBuffer.FillRandom()

        ssd.AtaCall28BitWritePio(dBuffer, sector * 512, 0xC0, 0x09, 0, 0, 0, 0, 0x31)

        return
