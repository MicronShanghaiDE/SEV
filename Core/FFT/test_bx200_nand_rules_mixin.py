import dm3
import sys
import time
from Util.decorator import method_tracer

class TestBX200NandRules:
    def set_up(self):
        self.unlock()
        self.ThrowException = True
        self.InterfaceMode = -1  # -1 indicates an unknown interface

    def tear_down(self):
        pass

    def genericNandCommand(self, nand_cmd, mode = 0, byte_size = 0, buf = None):
        ssd = self.ssd
        # @todo Need to figure out why a delay is needed to make this work.
        time.sleep(0.001)

        # Phase 1 command
        tfrBuf = dm3.Buffer(1)
        tfrBuf.FillZeros()
        buf_offset = 0
        self.assertLess(len(nand_cmd), 32, "Only 32 commands can fit into a single sector")
        # Initialize the transfer buffer with the command data.
        for tfr_entry in nand_cmd:
            self.assertLess(len(tfr_entry), 16, "Each command is padded to 16 bytes")
            tfrBuf.SetBytes(buf_offset, tfr_entry)
            buf_offset += 0x10

        # Send Phase 1 command to the drive
        cmd = dm3.sata.AtaCommand28BitWritePio(tfrBuf, 512, 0x10, 0x01, 0x00, 0x00, 0x00, 0xA0, 0xFA)
        # Adjust the context so that no exception is generated on call
        with dm3.DeviceContext(ssd.device, throwsExceptions = self.ThrowException):
            rsp = ssd.AtaCall(cmd)
        if not rsp.Success:
            return rsp

        # Send Phase 2 command to the drive
        if (mode == 1):
            # Read command
            self.assertGreater(byte_size, 0)
            sector_count = (int(byte_size) + 511) / 512  # Roundup sector count based on requested bytes
            if buf is None:
                buf = dm3.Buffer(sector_count)
                buf.FillZeros()
            cmd = dm3.sata.AtaCommand28BitReadPio(buf, sector_count * 512, 0x10, sector_count, byte_size & 0xFF, (byte_size >> 8) & 0xFF, (byte_size >> 16) & 0xFF, 0xA1, 0xFA)
            with dm3.DeviceContext(ssd.device, throwsExceptions = self.ThrowException):
                rsp = ssd.AtaCall(cmd)
            return buf
        elif (mode == 2):
            # Write command
            self.assertGreater(byte_size, 0)
            sector_count = (int(byte_size) + 511) / 512  # Roundup sector count based on requested bytes
            cmd = dm3.sata.AtaCommand28BitWritePio(buf, sector_count * 512, 0x10, sector_count, byte_size & 0xFF, (byte_size >> 8) & 0xFF, (byte_size >> 16) & 0xFF, 0xA2, 0xFA)
            # Adjust the context so that no exception is generated on call
            with dm3.DeviceContext(ssd.device, throwsExceptions = self.ThrowException):
                rsp = ssd.AtaCall(cmd)
            return rsp
        else:
            # None data command
            return rsp  # No need to send phase 2 command for no-data command

    @method_tracer()
    def nandResetNandInterface(self):
        '''
        Issues a RESET(0xFF) command to all NAND devices and sets the interface to default state (SDR)
        '''
        ssd = self.ssd
        # When enumerating through NAND, disable exceptions in case unpopulated channel touched
        exc_setting = self.ThrowException
        self.ThrowException = False
        # Go through all the NAND issue a RESET that will put the NAND into SDR mode
        for ch in xrange(0, ssd['max_ch']):
            for ce in xrange(0, ssd['max_ce']):
                cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
                cmd += ssd.nand.genericNandCmdDirectCmd(0xFF)  # Issue the Reset Command
                cmd += ssd.nand.genericNandCmdModeEnd(True)
                self.genericNandCommand(cmd)

        self.InterfaceMode = 0  # After reset, interface is in SDR(0) mode
        # Send a command to set the controller interface into SDR mode and poll for reset completion
        cmd = ssd.nand.genericNandCmdModeSetup(0, 0)  # Ch0/CE0 should exist on all drives
        cmd += ssd.nand.genericNandCmdInterfaceMode(self.InterfaceMode)  # Select the reset interface mode
        cmd += ssd.nand.genericNandCmdClkRate(35)  # Select the default timing mode
        cmd += ssd.nand.genericPollDirectStatus()  # Wait for reset to complete
        cmd += ssd.nand.genericNandCmdModeEnd(True)
        self.genericNandCommand(cmd)
        # Resetore the exception flag
        self.ThrowException = exc_setting
        return

    @method_tracer()
    def nandSetInterfaceMode(self, mode, freq = None):
        '''
            Sets the NAND interface's mode (sdr/ddr/ddr2) and adjusts the interface frequency
            If the current interface is not known, a reset is issued to return the NAND to a known state
            Note: this changes the state across all NAND devices.
        '''
        ssd = self.ssd
        modes = {'sdr' : 0, 'ddr' : 1, 'ddr2' : 2, 'ddr3' : 3}
        self.assertTrue(modes[mode] == modes['sdr'] or modes[mode] == modes['ddr'])  # Only supporting these mode in code

        # Determine the default frequency and the correpsonding timing mode
        if modes[mode] == modes['sdr']:
            f = 35 if freq == None else freq
            op_mode = ssd.nand.nandGetSDRTimingMode(f)
        else:
            f = 200 if freq == None else freq
            op_mode = ssd.nand.nandGetDDRTimingMode(f)
        # Formats op mode and target mode into the timing mode registers described in ONFI spec.
        timing_mode = (modes[mode] << 4) | op_mode

        # Only switch mode if not already in the selected mode
        if modes[mode] != self.InterfaceMode:
            # When going from nvddr back to sdr, use reset according to onfi spec
            if modes[mode] == modes['sdr'] or self.InterfaceMode == -1:
                self.nandResetNandInterface()

            # When enumerating through NAND, disable exceptions in case unpopulated channel touched
            exc_setting = self.ThrowException
            self.ThrowException = False
            # Go through all the NAND and update the timing mode register to reflect the target mode
            for ch in xrange(0, ssd['max_ch']):
                for ce in xrange(0, ssd['max_ce']):
                    cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
                    # Write the Timing Mode register
                    cmd += ssd.nand.genericNandCmdSetFeature(0x01, timing_mode)
                    cmd += ssd.nand.genericNandCmdModeEnd(True)
                    self.genericNandCommand(cmd)
            # Restore the throw excepting setting
            self.ThrowException = exc_setting

        # Last operation is to switch controller to new operating mode
        cmd = ssd.nand.genericNandCmdModeSetup(0, 0)  # Arbitrarly chose ch/ce0 which should always exist
        cmd += ssd.nand.genericNandCmdInterfaceMode(mode)  # Switch controller Mode to target mode
        cmd += ssd.nand.genericNandCmdClkRate(f)  # Switch the latching frequency
        cmd += ssd.nand.genericPollDirectStatus()  # Poll status for device to become ready
        cmd += ssd.nand.genericNandCmdModeEnd(True)
        cmd += ssd.nand.genericNandTestModeRelease()
        self.genericNandCommand(cmd)

        # Update the interface mode to now reflect the new state
        self.InterfaceMode = modes[mode]
        return

    def disable_all_ch_ce(self):
        ssd = self.ssd
        # Disable exceptions when enumerating (expect to get errors)
        exc_setting = self.ThrowException
        self.ThrowException = False

        # Loop through all channels
        for ch in xrange(ssd['max_ch']):
            cmd = ssd.nand.genericNandCmdDisableOneCh(ch)
            self.genericNandCommand(cmd)

        # Restore exceptions after getting through the NAND
        self.ThrowException = exc_setting
        return

    @method_tracer()
    def hmlcx7_histogram_read(self, ch, ce, lun = 0, blk = 0, page = 0, length = 74368, offset = None):
        ssd = self.ssd
        self.assertTrue((ch != 255) or (ce != 255) or (lun != 255) or (blk != 65535) or (page != 65535))
        self.disable_all_ch_ce()  # JIRA: BX200-156
        tlc_start_blk = self.get_tlc_start_block()
        if blk < tlc_start_blk:
            print "Current block is SLC block"
        else:
            print "Current block is TLC block"

        mode = 0x47  # ONFi 0x47 HMLCx7 Histogram Read Command

        # Convert the address parameters into the corresponding row address
        row_addr = (lun << ssd['LunStartBit']) | (blk << ssd['BlockStartBit']) | (page << ssd['PageStartBit'])

        if offset == None:
            offset = 0

        req_tfr = length  # Keep Track of original read request length
        if length > (64 * 1024):
            # Windows USB driver can only transfer 64KB,
            length = 64 * 1024

        # Issue the direct UID Command
        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericNandCmdDirectCmd(mode)  # Issue the cmd to set the read mode
        # The tMODE time duration is ~25ns.
        cmd += ssd.nand.genericNandCmdDirectCmd(0x00)  # Issue the read page cmd
        cmd += ssd.nand.genericNandCmdDirectAddr(offset, 2)  # Issue col addr
        cmd += ssd.nand.genericNandCmdDirectAddr(row_addr, 3)  # Issue row addr
        cmd += ssd.nand.genericNandCmdDirectCmd(0x30)  # Complete the read page cmd
        cmd += ssd.nand.genericPollDirectStatus()  # Wait for read to complete
        cmd += ssd.nand.genericNandCmdDirectCmd(0x00)  # Put NAND back in read mode
        cmd += ssd.nand.genericNandCmdModeEnd()

        # Send command and read the data from the buffer
        buf = self.genericNandCommand(cmd, 1, length)

        # If more data in page, then issue a col change and read data
        if length < req_tfr:
            # Low level API has a limit of 64KB transfers, so read partial page data
            # There are only 9296 column addresses on the B95A, no matter what mode you're in.
            # In HMLCx7 mode, eight bytes are output from every column address (7 for data, one dummy 0xff).
            col_addr = length / 8
            cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
            cmd += ssd.nand.genericNandCmdDirectCmd(0x05)  # Change Read Col
            cmd += ssd.nand.genericNandCmdDirectAddr(col_addr, 2)  # Issue col addr
            cmd += ssd.nand.genericNandCmdDirectCmd(0xE0)  # Complete the col change
            cmd += ssd.nand.genericNandCmdModeEnd()
            # Send command and read the data from the buffer
            tmp = self.genericNandCommand(cmd, 1, (req_tfr - length))
            buf.Resize((buf.TotalBytes + tmp.TotalBytes) / 512)
            tmp.CopyTo(buf, 0, ((buf.TotalBytes - tmp.TotalBytes) / 512))

        # Release CE after reading the data
        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericNandCmdModeEnd(True)
        cmd += ssd.nand.genericNandTestModeRelease()
        self.genericNandCommand(cmd)

        # Go through each chunk of histogram data
        # Copy the chunk of histogram data into a buffer
        data_chunk = dm3.Buffer((buf.TotalBytes + 511) / 512)
        data_chunk.FillZeros()
        for offset in xrange(0, req_tfr, 8):
            # Go through the 7 bytes (byte 7 is dummy) of histogram data and separate the bits into 8 dac voltages
            for ii in xrange(0, 7):
                val = buf.GetByte(offset + ii);
                for jj in xrange(0, 8):
                    tmp = data_chunk.GetByte(offset + jj)
                    tmp = (tmp << 1) | (val & 1)
                    val >>= 1
                    data_chunk.SetByte(offset + jj, tmp)
        return data_chunk

    # @method_tracer()
    def tlc_program(self, ch, ce, lun, blk, page, dbuffer, byte_size = 27888, mode = 0x43):
        ssd = self.ssd
        self.assertTrue((ch != 255) or (ce != 255) or (lun != 255) or (blk != 65535) or (page != 65535))

        if mode == 0x41:
            msg = "TLC Coarse program"
        elif mode == 0x42:
            msg = "TLC Fine program"
        elif mode == 0x43:
            msg = "TLC Super Fine program"
        elif mode == 0x40:
            msg = "SLC program"
        else:
            print "Invalid program mode"
            return

        print "Program data on ch: %d, ce: %d, lun: %d, blk: %d, page: %d using %s mode" % (ch, ce, lun, blk, page, msg)
        self.disable_all_ch_ce()  # JIRA: BX200-156

        # Convert the address parameters into the corresponding row address
        row_addr = (lun << ssd['LunStartBit']) | (blk << ssd['BlockStartBit']) | (page << ssd['PageStartBit'])

        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericNandCmdDirectCmd(mode)  # Issue the cmd to set the program mode
        cmd += ssd.nand.genericNandCmdDirectCmd(0x80)  # Issue the program page cmd
        cmd += ssd.nand.genericNandCmdDirectAddr(0, 2)  # Issue col addr (offset within page)
        cmd += ssd.nand.genericNandCmdDirectAddr(row_addr, 3)  # Issue row addr
        cmd += ssd.nand.genericNandCmdModeEnd()
        self.genericNandCommand(cmd, 2, byte_size, dbuffer)

        # Send a command to poll status for completion
        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericNandCmdDirectCmd(0x10)  # Issue the second part of the program page cmd
        cmd += ssd.nand.genericPollDirectStatus()
        cmd += ssd.nand.genericNandCmdModeEnd(True)
        self.genericNandCommand(cmd)
        return

    def tlc_one_block_program(self, ch, ce, lun, blk, dBuffer):
        ssd = self.ssd
        for page_group, prog_type in ssd['page_table']:
            for page in page_group:
                if prog_type == "tlc_coarse":
                    mode = 0x41
                    byte_size = ssd['PageByteTLC']
                    self.tlc_program(ch, ce, lun, blk, page, dBuffer, byte_size, mode)
                elif prog_type == "tlc_fine":
                    mode = 0x42
                    byte_size = ssd['PageByteTLC']
                    self.tlc_program(ch, ce, lun, blk, page, dBuffer, byte_size, mode)
                elif prog_type == "tlc_superfine":
                    mode = 0x43
                    byte_size = ssd['PageByteTLC']
                    self.tlc_program(ch, ce, lun, blk, page, dBuffer, byte_size, mode)
                else:  # SLC program
                    mode = 0x40
                    byte_size = ssd['PageByteSLC']
                    slc_dBuffer = dm3.Buffer((ssd['PageByteSLC'] + 511) / 512)
                    slc_dBuffer.FillRandom()
                    self.tlc_program(ch, ce, lun, blk, page, slc_dBuffer, byte_size, mode)

    @method_tracer()
    def static_trim_read(self, ch, ce, lun, addr):
        ssd = self.ssd
        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericPollDirectStatusEnhanced(lun << ssd['LunStartBit'])
        cmd += ssd.nand.genericNandCmdEnterLvcm()
        cmd += ssd.nand.genericPollDirectStatus()
        cmd += ssd.nand.genericNandCmdStaticTrimSpaceAccess()
        cmd += ssd.nand.genericNandCmdDirectAddr(addr)
        cmd += ssd.nand.genericNandCmdModeEnd()
        buf = self.genericNandCommand(cmd, mode = 1, byte_size = 1)
        val = buf.GetByte(0)

        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericNandCmdStaticTrimSpaceExit()
        cmd += ssd.nand.genericNandCmdExitLvcm()
        cmd += ssd.nand.genericNandCmdModeEnd(True)
        self.genericNandCommand(cmd)
        return val

    @method_tracer()
    def static_trim_write(self, ch, ce, lun, addr, data):
        ssd = self.ssd
        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericPollDirectStatusEnhanced(lun << ssd['LunStartBit'])
        cmd += ssd.nand.genericNandCmdEnterLvcm()
        cmd += ssd.nand.genericPollDirectStatus()
        cmd += ssd.nand.genericNandCmdStaticTrimSpaceAccess()
        cmd += ssd.nand.genericNandCmdDirectAddr(addr)
        cmd += ssd.nand.genericNandCmdDirectData(data)  # Value for input
        cmd += ssd.nand.genericNandCmdModeEnd()
        self.genericNandCommand(cmd)

        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericNandCmdStaticTrimSpaceExit()
        cmd += ssd.nand.genericNandCmdExitLvcm()
        cmd += ssd.nand.genericNandCmdModeEnd(True)
        self.genericNandCommand(cmd)
        return

    @method_tracer()
    def read_trim_register(self, ch, ce, lun, reg_param, reg_addr, test_mode = False):
        ssd = self.ssd
        if not test_mode:
            # Uses the MLBi GetTrim command to access the trim registers
            # Mask out the Write ALL_LUNs flag from the trim param table
            reg_param &= 0x7F
            # Select test mode, ce and ch.
            cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
            # Poll LUN status to make sure its ready
            cmd += ssd.nand.genericPollDirectStatusEnhanced(lun << ssd['LunStartBit'])
            cmd += ssd.nand.genericNandCmdDirectCmd(0xEA)
            cmd += ssd.nand.genericNandCmdDirectAddr([reg_addr, reg_param, lun << 4])
            cmd += ssd.nand.genericNandCmdModeEnd()
            buf = self.genericNandCommand(cmd, mode = 1, byte_size = 1)
            val = buf.GetByte(0)
            # Send command to release CE otherwise it will stay asserted when data read
            cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
            cmd += ssd.nand.genericNandCmdModeEnd(True)
            self.genericNandCommand(cmd)
        else:
            # Select test mode, ce and ch.
            cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
            cmd += ssd.nand.genericPollDirectStatusEnhanced(lun << ssd['LunStartBit'])
            cmd += ssd.nand.genericNandCmdEnterLvcm()
            cmd += ssd.nand.genericNandCmdTrimValues(reg_param, reg_addr)
            cmd += ssd.nand.genericNandCmdModeEnd()
            # Now actually send the built command to the drive, trim value is returned
            buf = self.genericNandCommand(cmd, mode = 1, byte_size = 1)
            val = buf.GetByte(0)

            # Create the command that disables the trim page and disables the LVCM mode, and releases CE
            cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
            cmd += ssd.nand.genericNandEndTrimValues()
            cmd += ssd.nand.genericNandCmdExitLvcm()
            cmd += ssd.nand.genericNandCmdModeEnd(True)
            self.genericNandCommand(cmd)
        return val

    @method_tracer()
    def write_trim_register(self, ch, ce, lun, reg_param, reg_addr, data, test_mode = False):
        ssd = self.ssd
        if not test_mode:
            # Uses the MLBi GetTrim command to access the trim registers
            # Mask out the Write ALL_LUNs flag from the trim param table
            reg_param &= 0x7F
            # Select test mode, ce and ch.
            cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
            # Poll LUN status to make sure its ready
            cmd += ssd.nand.genericPollDirectStatusEnhanced(lun << ssd['LunStartBit'])
            cmd += ssd.nand.genericNandCmdDirectCmd(0xEB)
            cmd += ssd.nand.genericNandCmdDirectAddr([reg_addr, reg_param, lun << 4])
            cmd += ssd.nand.genericNandCmdDirectData(data)
            cmd += ssd.nand.genericNandCmdModeEnd(True)
            self.genericNandCommand(cmd)
        else:
            # Select test mode, ce and ch.
            cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
            self.genericNandCommand(cmd)
        return

    @method_tracer()
    def unlock(self):
        ssd = self.ssd
        ssd.AtaCall28BitNoData(0x55, 0x41, 0x75, 0x67, 0x30, 0xA0, 0xFA)
        return

    def bist_execution(self):
        ssd = self.ssd
        ssd.AtaCall28BitNoData(0x90, 0, 0, 0, 0, 0xA0, 0xFA)
        return

    @method_tracer()
    def get_tlc_start_block(self):
        ssd = self.ssd
        fwBuf = dm3.Buffer(2)
        fwBuf.FillZeros()
        ssd.AtaCall28BitReadPio(fwBuf, 1024, 0x21, 0x02, 0x00, 0x00, 0x00, 0xA0, 0xFA)
        return ((fwBuf.GetByte(16) << 8) + fwBuf.GetByte(17))

    @method_tracer()
    def translate_lba(self, lba):
        ssd = self.ssd
        print "Translate LBA %d to physical address" % lba
        lba0 = lba & 0xff
        lba1 = (lba >> 8) & 0xff
        lba2 = (lba >> 16) & 0xff
        lba3 = (lba >> 24) & 0xff

        ssd.AtaCall28BitNoData(0x34, 0x00, lba3, 0xEC, 0x48, 0xA0, 0xFA)

        rBuffer = dm3.Buffer(1)
        rBuffer.FillZeros()
        ssd.AtaCall28BitReadPio(rBuffer, 512, 0x34, 0x01, lba0, lba1, lba2, 0xA0, 0xFA)

        ch = rBuffer.GetByte(0)
        ce = rBuffer.GetByte(1)
        blk = rBuffer.GetByte(2) + (rBuffer.GetByte(3) << 8)
        page = rBuffer.GetByte(4) + (rBuffer.GetByte(5) << 8)
        lun = rBuffer.GetByte(6)

        print "Physical address for LBA %d is ch: %d, ce: %d, lun: %d, blk: %d, page: %d" % (lba, ch, ce, lun, blk, page)

        return (ch, ce, blk, page, lun)

    @method_tracer()
    def read_direct(self, ch, ce, lun, blk, page, byte_size, mode = 3):
        ssd = self.ssd
        ceChan = ((ce << 4) | ch)
        row_addr = (lun << ssd['LunStartBit']) | (blk << ssd['BlockStartBit']) | (page << ssd['PageStartBit'])
        acyc3 = row_addr & 0xFF
        acyc4 = (row_addr >> 8) & 0xFF
        acyc5 = (row_addr >> 16) & 0xFF
        sector = (byte_size + 511) / 512

        print "Read Direct Phase 1"
        ssd.AtaCall28BitNoData(0x70, (byte_size & 0xFF), ((byte_size >> 8) & 0xFF), ceChan, 0xEC, 0xA0, 0xFA)

        print "Read Direct Phase 2"
        mode |= 0xA0
        rBuffer = dm3.Buffer(sector)
        rBuffer.FillZeros()
        ssd.AtaCall28BitReadPio(rBuffer, sector * 512, 0x70, sector, acyc3, acyc4, acyc5, mode, 0xFA)

        return rBuffer

    @method_tracer()
    def erase_direct(self, ch, ce, lun, blk, page = 0, mode = 3):
        ssd = self.ssd
        ceChan = ((ce << 4) | ch)
        row_addr = (lun << ssd['LunStartBit']) | (blk << ssd['BlockStartBit']) | (page << ssd['PageStartBit'])
        acyc3 = row_addr & 0xFF
        acyc4 = (row_addr >> 8) & 0xFF
        acyc5 = (row_addr >> 16) & 0xFF
        mode |= 0xA0

        print "Erase Direct on ch: %d, ce: %d, lun: %d, blk: %d" % (ch, ce, lun, blk)
        ssd.AtaCall28BitNoData(0x67, ceChan, acyc3, acyc4, acyc5, mode, 0xFA)

        return

    @method_tracer()
    def get_error_recovery_statistics(self, die_count):
        ssd = self.ssd

        # BX200 max_ch * max_ce * max_lun * info_per_die
        sector_count = (8 * 4 * 2 * 160 + 511) / 512
        rBuffer = dm3.Buffer(sector_count)
        rBuffer.FillZeros()

        ssd.AtaCall28BitReadPio(rBuffer, sector_count * 512, 0x94, sector_count, 0, 0, 0, 0xA0, 0xFA)
        dic = self.error_recovery_statistics_parser(die_count, rBuffer)
        """
        RR16 means Soft Decode
        RR17 means Super Calibration-RR0
        RR18 means Target Calibration-RR0-Soft Decode
        RR19 means RAID
        """
        for rr in xrange(20):
            name = "RR%d" % rr
            if name == "RR16":
                name = "soft"
            elif name == "RR17":
                name = "sCal"
            elif name == "RR18":
                name = "t-pCal"
            elif name == "RR19":
                name = "RAID"
            else:
                name = name
            print "%4s" % name,
        print "\n",

        for die in xrange(die_count):
            for rr in xrange(20):
                name = "Die %d Success Hard Decode-RR%x" % (die, rr)
                print "%4d" % dic[name],
            print "\n",

    @method_tracer()
    def trigger_recalibration(self):
        ssd = self.ssd
        rBuffer = dm3.Buffer(1)
        with dm3.DeviceContext(ssd.device, commandTimeOut = 300, throwsExceptions = self.ThrowException):
            ssd.AtaCall28BitReadPio(rBuffer, 512, 0x97, 1, 0, 0, 0, 0xA0, 0xFA)
        return (rBuffer.GetWord(0), rBuffer.GetWord(1))

    @method_tracer()
    def get_target_page_calibration_info(self):
        ssd = self.ssd

        rBuffer = dm3.Buffer(16)
        rBuffer.FillZeros()
        ssd.AtaCall28BitReadPio(rBuffer, 16 * 512, 0x99, 16, 0, 0, 0, 0, 0xFA)
        print rBuffer

        print "%3s %2s %2s %3s %5s %5s %4s %7s %7s %10s" % ('id', 'ch', 'ce', 'lun', 'plane', 'block', 'page', 't_after', 't_before', 'offset')
        for offset in xrange(0, 16 * 512, 32):
            blk = rBuffer.GetWord(offset)
            page = rBuffer.GetWord(offset + 2)
            ch = rBuffer.GetByte(offset + 4)
            ce = rBuffer.GetByte(offset + 5)
            plane = rBuffer.GetByte(offset + 6)
            lun = rBuffer.GetByte(offset + 7)
            cal_offset = rBuffer.GetBytes(offset + 8, 7)
            for i in xrange(len(cal_offset)):
                if cal_offset[i] > 128:
                    cal_offset[i] -= 256
            t_after = rBuffer.GetByte(offset + 15)
            t_before = rBuffer.GetByte(offset + 16)
            execute_count = rBuffer.GetWord(offset + 30)
            if any((execute_count, ch, ce, lun, plane, blk, page)) != 0:
                print "%3d %2d %2d %3d %5d %5d %4d %7d %7d %10s" % (execute_count, ch, ce, lun, plane, blk, page, t_after, t_before, cal_offset)

    def error_recovery_statistics_parser(self, die_count, buf):
        statistics_success_dic = {}
        for die in xrange(die_count):
            for rr in xrange(20):
                name = "Die %d Success Hard Decode-RR%x" % (die, rr)
                statistics_success_dic[name] = 0
        die = 0
        for die_offset in xrange(0, 64 * 160, 160):
            # No error recovery statistics for 240/480 on LUN 1
            if (((die_count == 16) or (die_count == 32)) and ((die_offset / 160) % 2 != 0)):
                continue
            # No ce 4~7 for 240
            if ((die_count == 16) and (((die_offset / 160) / 8) % 2) == 1):
                continue
            for offset in xrange(0, 0x50, 0x04):
                name = "Die %d Success Hard Decode-RR%x" % (die, offset / 0x04)
                statistics_success_dic[name] = buf.GetByte(die_offset + offset) + (buf.GetByte(die_offset + offset + 1) << 8) \
                                             + (buf.GetByte(die_offset + offset + 2) << 16) + (buf.GetByte(die_offset + offset + 3) << 24)
            die += 1
        return statistics_success_dic

    @method_tracer()
    def get_one_page_histogram_valley(self, ch, ce, lun, blk, page):
        ssd = self.ssd
        self.disable_all_ch_ce()
        mode = 0x47  # ONFi 0x47 HMLCx7 Histogram Read Command

        # Convert the address parameters into the corresponding row address
        row_addr = (lun << ssd['LunStartBit']) | (blk << ssd['BlockStartBit']) | (page << ssd['PageStartBit'])

        req_tfr = 74368  # Keep Track of original read request length
        length = 64 * 1024

        # Issue the direct UID Command
        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericNandCmdDirectCmd(mode)  # Issue the cmd to set the read mode
        # The tMODE time duration is ~25ns.
        cmd += ssd.nand.genericNandCmdDirectCmd(0x00)  # Issue the read page cmd
        cmd += ssd.nand.genericNandCmdDirectAddr(0, 2)  # Issue col addr
        cmd += ssd.nand.genericNandCmdDirectAddr(row_addr, 3)  # Issue row addr
        cmd += ssd.nand.genericNandCmdDirectCmd(0x30)  # Complete the read page cmd
        cmd += ssd.nand.genericPollDirectStatus()  # Wait for read to complete
        cmd += ssd.nand.genericNandCmdDirectCmd(0x00)  # Put NAND back in read mode
        cmd += ssd.nand.genericNandCmdModeEnd()

        # Send command and read the data from the buffer
        buf = self.genericNandCommand(cmd, 1, length)

        col_addr = length / 8
        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericNandCmdDirectCmd(0x05)  # Change Read Col
        cmd += ssd.nand.genericNandCmdDirectAddr(col_addr, 2)  # Issue col addr
        cmd += ssd.nand.genericNandCmdDirectCmd(0xE0)  # Complete the col change
        cmd += ssd.nand.genericNandCmdModeEnd()
        # Send command and read the data from the buffer
        tmp = self.genericNandCommand(cmd, 1, (req_tfr - length))
        buf.Resize((buf.TotalBytes + tmp.TotalBytes) / 512)
        tmp.CopyTo(buf, 0, ((buf.TotalBytes - tmp.TotalBytes) / 512))

        # Release CE after reading the data
        cmd = ssd.nand.genericNandCmdModeSetup(ce, ch)
        cmd += ssd.nand.genericNandCmdModeEnd(True)
        cmd += ssd.nand.genericNandTestModeRelease()
        self.genericNandCommand(cmd)

        # Go through each chunk of histogram data
        dac = {}
        for i in xrange(128):
            dac[i] = 0

        for offset in xrange(0, 74368, 8):
            # Go through the 7 bytes (byte 7 is dummy) of histogram data and separate the bits into 8 dac voltages
            dac_list = [0, 0, 0, 0, 0, 0, 0, 0]
            for ii in xrange(7):
                val = buf.GetByte(offset + ii);
                for jj in xrange(0, 8):
                    dac_list[jj] = (dac_list[jj] << 1) | (val & 1)
                    val >>= 1
            for ii in xrange(8):
                dac[127 - dac_list[ii]] += 1

        peak = [1, 31, 49, 63, 79, 94, 109, 128]
        valley = [0, 0, 0, 0, 0, 0, 0]

        for i in xrange(7):
            valley[i] = peak[i]
            value = dac[peak[i]]
            for dac_value in xrange(peak[i], peak[i + 1]):
                if dac[dac_value] < value:
                    valley[i] = dac_value
                    value = dac[dac_value]

        return valley, [dac[valley[0]], dac[valley[1]], dac[valley[2]], dac[valley[3]], dac[valley[4]], dac[valley[5]], dac[valley[6]]]

    def get_one_block_histogram_valley(self, ch, ce, lun, blk):
        ssd = self.ssd

        blk_valley = []
        for page in xrange(ssd['BlockPageTLC']):
            blk_valley.append(self.get_one_page_histogram_valley(ch, ce, lun, blk, page))

        for page in xrange(ssd['BlockPageTLC']):
            print "Block %d, Page %d" % (blk, page),
            print blk_valley[page]

        return

    def get_one_die_histogram_valley(self, ch, ce, lun):
        ssd = self.ssd

        tlc_start_blk = self.get_tlc_start_block()

        log_name = "CH_%d_CE_%d_LUN_%d.log" % (ch, ce, lun)
        saveout = sys.stdout
        fsock = open(log_name, 'w')
        sys.stdout = fsock

        for blk in xrange(tlc_start_blk, ssd['BlockPerDie'], 1):
            self.get_one_block_histogram_valley(ch, ce, lun, blk)

        sys.stdout = saveout
        fsock.close()

    def count_vt(self, buf, length = None):
        if length is None:
            length = buf.TotalBytes

        dic = {}
        for i in xrange(length):
            vt = 127 - buf.GetByte(i)
            if vt in dic.keys():
                dic[vt] += 1
            else:
                dic[vt] = 1
        return dic

    def draw_plot(self, *arg, **kwargs):
        import re
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print "matplotlib not installed on this machine"
        else:
            xlim = kwargs['xlim'] if 'xlim' in kwargs.keys() else 128
            ylim = kwargs['ylim'] if 'ylim' in kwargs.keys() else 3000
            plt.xlim(1, xlim)
            plt.ylim(1, ylim)
            plt.xlabel('DAC')
            plt.ylabel('Distribution')
            plt.title('VT Distribution')
            x = {}
            y = {}
            c = {}  # color
            timer = 0
            keys = kwargs.keys()
            keys.sort()
            for key in keys:
                if re.search('plot', key):
                    dic = kwargs[key]
                    dic = sorted(dic.iteritems(), key = lambda d:d[0], reverse = False)
                    x[key] = []
                    y[key] = []
                    if (timer % 3) == 0:
                        c[key] = 'r'
                    elif (timer % 3) == 1:
                        c[key] = 'b'
                    else:
                        c[key] = 'g'
                    timer += 1
                    for i in xrange(len(dic)):
                        x[key].append(dic[i][0])
                        y[key].append(dic[i][1])
            cmd = "plt.plot("
            for key in keys:
                if re.search('plot', key):
                    cmd += "x['%s'], y['%s'], c['%s'], " % (key, key, key)
            cmd += "linewidth = 2)"
            exec(cmd)
            plt.savefig('BX200_VT_Distribution.png', dpi = 500)
            plt.show()
            return

    def whole_block_histo(self, ch, ce, lun, blk):
        ssd = self.ssd
        blk_dic = {}
        for page in xrange(ssd['BlockPageTLC']):
            print "Get histo data in page %d" % page
            buf = self.hmlcx7_histogram_read(ch, ce, lun, blk, page)
            dic = self.count_vt(buf, ssd['histo_length'])
        return blk_dic
