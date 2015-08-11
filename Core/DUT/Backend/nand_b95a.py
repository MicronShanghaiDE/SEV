from Util.decorator import *
from Util.assertion import Assertion

class B95a(Assertion):
    def __init__(self, ssd):
        self.ssd = ssd
        self.ch = -1
        self.ce = -1

    def genericNandCmdModeSetup(self, ce, ch):
        cmd = ((0xA0, 0x01),)  # Enable Test Mode, required for each command
        # if channel or CE changes, then deselect it
        if self.ch != -1 and (self.ce != ce or self.ch != ch):
            cmd += ((0xA2, self.ce, 0x00),)  # Deselect the current CE
            self.ce = -1
            self.ch = -1
        self.assert_true(self.ce == -1 or self.ce == ce, "By design, only expect one ch/ce to be selected")
        self.assert_true(self.ch == -1 or self.ch == ch, "By design, only expect one ch/ce to be selected")

        # @todo Add code to not send the CE/CH if they are already set
        self.ce = ce
        self.ch = ch  # @todo Does ch need to be sent in every command? or is there any deselection?
        cmd += ((0xA1, ch),  # Set channel
                (0xA2, ce, 0x01),)  # Enable CE
        return cmd

    def genericNandTestModeRelease(self):
        cmd = ((0xA0, 0x00),)
        return cmd

    def genericNandCmdDirectCmd(self, cmd, cmd_len = 1):
        if isinstance(cmd, int):  # Create entry based on a integer input
            entry = (0xA3, cmd_len)  # Add the command and length of the command
            for b in range(0, cmd_len * 8, 8):
                entry += ((cmd >> b) & 0xFF,)  # append the command
        elif isinstance(cmd, tuple) or isinstance(cmd, list):  # Create entry based on tuple/list
            entry = (0xA3, len(cmd))  # Add the command and length of command bytes
            for b in cmd:
                entry += (b,)
        else:
            self.assert_failed("Unrecognized type")
        return (entry,)

    def genericNandCmdDirectAddr(self, addr, addr_len = 1):
        if isinstance(addr, int):  # Create entry based on a integer input
            entry = (0xA4, addr_len)  # Add the command and length of the address
            for b in range(0, addr_len * 8, 8):
                entry += ((addr >> b) & 0xFF,)  # append the address bytes into the array
        elif isinstance(addr, tuple) or isinstance(addr, list):  # Create entry based on tuple/list
            entry = (0xA4, len(addr))  # Add the command and length of address bytes
            for b in addr:
                entry += (b,)
        else:
            self.assert_failed("Unrecognized type")
        return (entry,)

    def genericNandCmdDirectData(self, val, val_len = 1):
        entry = ()
        if isinstance(val, int):  # Create entry based on a integer input
            for b in range(0, val_len * 8, 8):
                entry += (0xA5, (val >> b) & 0xFF),
        elif isinstance(val, tuple) or isinstance(val, list):  # Create entry based on tuple/list
            for b in val:
                entry += (0xA5, b),
        else:
            self.assert_failed("Unrecognized type")
        return entry

    def genericNandCmdInterfaceMode(self, mode):
        mode_trans = {'sdr' : 0, 'ddr' : 1, 'ddr2' : 2, 'ddr3' : 3}
        if not isinstance(mode, int):
            mode = mode_trans[mode]
        return ((0xA6, mode),)  # Command to FW to indicate it's operating mode

    def genericNandCmdClkRate(self, freq):
        freq_trans = {20: 0x02, 35 : 0x9A, 50 : 0x08, 60 : 0x0a, 70 : 0xC, 80 : 0x0e, 100 : 0x12, 105 : 0x13, 110 : 0x14,
                      115 : 0x15, 120 : 0x16, 125 : 0x17, 130 : 0x18, 135 : 0x19, 140 : 0x1A, 145 : 0x1B, 150 : 0x1C,
                      155 : 0x1D, 160 : 0x1E, 165 : 0x1F, 170 : 0x20, 175 : 0x21, 180 : 0x22, 185 : 0x23, 190 : 0x24,
                      195 : 0x25, 200 : 0x26}
        return ((0xA7, freq_trans[freq]),)  # Command to FW to indicate the operating frequency.  For DDR mode this is 2x data rate

    def genericNandReadStatus(self):
        return ((0xA8, 0),)  # Tells FW/controller to poll status for ready/busy to indicate ready

    def genericNandCmdModeEnd(self, release_ce = False):
        self.assert_not_equal(-1, self.ce, "Should be a selected Chip Enable by this point")
        self.assert_not_equal(-1, self.ch, "Should be a selected Channel by this point")
        cmd = ()
        if release_ce:
            # Deselect CE if requested by the caller
            cmd += ((0xA2, self.ce, 0),)  # Add command to deselect CE of device
            self.ce = -1
            self.ch = -1
        cmd += ((0xA9, 0),)  # Complete the command list
        return cmd

    def genericNandCmdEnterLvcm(self):
        '''
            Returns the command sequence for enabling Low Voltage Test Mode (LVCM)
        '''
        return self.genericNandCmdDirectCmd((0xB9, 0xF7, 0xA8, 0x1F, 0x88, 0x0F, 0xB4, 0xE3, 0xCD, 0x2A, 0x16, 0x69))

    def genericNandCmdExitLvcm(self):
        '''
            Returns the command sequence for disabling LVCM Test Mode
        '''
        return self.genericNandCmdDirectCmd(0xCF)

    def genericNandCmdStaticTrimSpaceAccess(self):
        cmd = self.genericNandCmdDirectCmd(0x0d)  # SRAM space selector
        cmd += self.genericNandCmdDirectAddr(0x00)
        cmd += self.genericNandCmdDirectData(0x05)  # Value for static trim access
        cmd += self.genericNandCmdDirectCmd(0x0b)  # SRAM data input/output enable
        return cmd

    def genericNandCmdStaticTrimSpaceExit(self):
        cmd = self.genericNandCmdDirectCmd(0x0d)  # SRAM space selector
        cmd += self.genericNandCmdDirectAddr(0x00)
        cmd += self.genericNandCmdDirectData(0x00)
        cmd += self.genericNandCmdDirectCmd(0xff)  # A reset, just to make sure everything is cleaned up
        return cmd

    def genericNandCmdTrimValues(self, param, addr):
        cmd = self.genericNandCmdDirectCmd(0x0B)  # Command to indicate address is for reg_table
        cmd += self.genericNandCmdDirectAddr(0x0E)  # Address command to enable rom access and indicate data to select ROM page
        cmd += self.genericNandCmdDirectData(param)  # Selects the ROM page PARAM1=0x10, PARAM2=0x11, PARAM3=0x12
        cmd += self.genericNandCmdDirectCmd(0x0D)  # Command to indicate address cycle selects ROM page register address
        cmd += self.genericNandCmdDirectAddr(addr)  # Latch ROM page register address (00h-ffh)
        return cmd

    def genericNandEndTrimValues(self):
        cmd = self.genericNandCmdDirectCmd(0x0B)  # Command to indicate address is for reg_table
        cmd += self.genericNandCmdDirectAddr(0x0E)  # Address command to enable rom access and indicate data to select a ROM page
        cmd += self.genericNandCmdDirectData(0x00)  # Reset ROM page selection to 0 to release any previously selected param page
        return cmd

    def genericNandCmdSetFeature(self, f_addr, f_param):
        '''
            Returns the encoded set feature command in the generic NAND command protocol
        '''
        self.assert_true(f_addr >= 0 and f_addr < 256, "Feature address is only a byte")
        cmd = self.genericNandCmdDirectCmd(0xEF)  # Set Feature Cmd
        cmd += self.genericNandCmdDirectAddr(f_addr)  # ALE Cycle Feature Addr
        cmd += self.genericNandCmdDirectData(f_param, 4)  # Write Byte Sub Feature Param1
        return cmd

    def genericNandCmdDisableOneCh(self, ch):
        ssd = self.ssd
        cmd = ((0xA0, 0x01),)  # Set the Test Mode Enable Command (required by interface)
        cmd += ((0xA1, ch),)  # Select the Channel
        # Create a command that clears all chip enables
        for ce in xrange(ssd['max_ce']):
            cmd += ((0xA2, ce, 0x00),)  # Deassert the chip enable
        cmd += ((0xA0, 0x00),)  # Exit Test Mode
        cmd += ((0xA9, 0),)  # Complete the command
        return cmd

    def genericPollDirectStatus(self):
        cmd = self.genericNandCmdDirectCmd(0x70)  # Send Status command
        cmd += self.genericNandReadStatus()  # Tell controller to poll status
        return cmd

    def genericPollDirectStatusEnhanced(self, row_addr):
        '''
            Adds command to get the NAND's enhanced status and issues a command to poll until ready
        '''
        cmd = self.genericNandCmdDirectCmd(0x78)  # Send Enh Status command
        cmd += self.genericNandCmdDirectAddr(row_addr, 3)
        cmd += self.genericNandReadStatus()  # Tell controller to poll status
        return cmd

    def nandGetSDRTimingMode(self, freq):
        '''
        Converts the specified frequency to an equivalent SDR mode timing.  Mode timing range determined
        from the "Timing Modes" values specified in the ONFI Specification
        '''
        if freq >= 100:
            op_mode = 5
        elif freq >= 83:
            op_mode = 4
        elif freq >= 66:
            op_mode = 3
        elif freq >= 50:
            op_mode = 2
        elif freq >= 33:
            op_mode = 1
        else:
            op_mode = 0
        return op_mode

    def nandGetDDRTimingMode(self, freq):
        '''
        Converts the specified frequency to an equivalent DDR mode timing.  Mode timing range determined
        from the "Timing Modes" values specified in the ONFI Specification
        '''
        if freq >= 100 * 2:
            op_mode = 5
        elif freq >= 83 * 2:
            op_mode = 4
        elif freq >= 66 * 2:
            op_mode = 3
        elif freq >= 50 * 2:
            op_mode = 2
        elif freq >= 33 * 2:
            op_mode = 1
        else:
            op_mode = 0
        return op_mode




