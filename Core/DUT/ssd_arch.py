from Util.assertion import Assertion
from Util.decorator import method_tracer

class SSDArch(Assertion):
    @classmethod
    def arch(cls, arch_name):
        '''Factory function to 'instance' the arch cls
        '''
        module = __import__('DUT.ssd_arch', fromlist = 'DUT')
        for name, value in module.__dict__.items():
            if name == arch_name and issubclass(value, SSDArch):
                return value

        return None

    @method_tracer(silent = True)
    def __init__(self, ssd):
        self.power_cycle_limit = 60
        self.max_sectors_per_read_write = 256
        self.sectors_per_fi_chunk = 8

class MauiArch(SSDArch):
    def __init__(self, ssd):
        SSDArch.__init__(self, ssd)
        self.abbreviation = 'Maui'
        self.BlockStartBit = 7
        self.LunStartBit = 19
        self.PageStartBit = 0
        self.max_ch = 4
        identify_data = ssd.IdentifyDevice()
        max_lba = identify_data.TotalLbas
        if max_lba == 15649200:
            self.max_ce = 1
        elif max_lba == 31277232:
            self.max_ce = 2

class BX200Arch(SSDArch):
    def __init__(self, ssd):
        SSDArch.__init__(self, ssd)
        self.abbreviation = 'BX200'
        self.BlockStartBit = 8
        self.BlockPageTLC = 252
        self.histo_length = 74368  # default value for 0x47 mode
        self.LunStartBit = 20
        self.PageByteSLC = 9296
        self.PageByteTLC = 27888
        self.PageStartBit = 0
        self.max_ch = 4
        self.BlockPerDie = 2762

        identify_data = ssd.IdentifyDevice()
        model = identify_data.Model.replace(' ', '')
        import re
        if re.search('240', model):
            self.max_ce = 4
            self.max_lun = 1
        elif re.search('480', model):
            self.max_ce = 8
            self.max_lun = 1
        elif re.search('960', model):
            self.max_ce = 8
            self.max_lun = 2

        self.page_table = (
            ((0, 1, 2, 3, 4, 5), 'tlc_coarse'), ((0, 1, 2, 3), 'tlc_fine'), ((0, 1), 'tlc_superfine'),
            ((6, 7), 'tlc_coarse'), ((4, 5), 'tlc_fine'), ((2, 3), 'tlc_superfine'),
            ((8, 9), 'tlc_coarse'), ((6, 7), 'tlc_fine'), ((4, 5), 'tlc_superfine'),
            ((10, 11), 'tlc_coarse'), ((8, 9), 'tlc_fine'), ((6, 7), 'tlc_superfine'),
            ((12, 13), 'tlc_coarse'), ((10, 11), 'tlc_fine'), ((8, 9), 'tlc_superfine'),
            ((14, 15), 'tlc_coarse'), ((12, 13), 'tlc_fine'), ((10, 11), 'tlc_superfine'),
            ((16, 17), 'tlc_coarse'), ((14, 15), 'tlc_fine'), ((12, 13), 'tlc_superfine'),
            ((18, 19), 'tlc_coarse'), ((16, 17), 'tlc_fine'), ((14, 15), 'tlc_superfine'),
            ((20, 21), 'tlc_coarse'), ((18, 19), 'tlc_fine'), ((16, 17), 'tlc_superfine'),
            ((22, 23), 'tlc_coarse'), ((20, 21), 'tlc_fine'), ((18, 19), 'tlc_superfine'),
            ((24, 25), 'tlc_coarse'), ((22, 23), 'tlc_fine'), ((20, 21), 'tlc_superfine'),
            ((26, 27), 'tlc_coarse'), ((24, 25), 'tlc_fine'), ((22, 23), 'tlc_superfine'),
            ((28, 29), 'tlc_coarse'), ((26, 27), 'tlc_fine'), ((24, 25), 'tlc_superfine'),
            ((30, 31), 'tlc_coarse'), ((28, 29), 'tlc_fine'), ((26, 27), 'tlc_superfine'),
            ((32, 33), 'tlc_coarse'), ((30, 31), 'tlc_fine'), ((28, 29), 'tlc_superfine'),
            ((34, 35), 'tlc_coarse'), ((32, 33), 'tlc_fine'), ((30, 31), 'tlc_superfine'),
            ((36, 37), 'tlc_coarse'), ((34, 35), 'tlc_fine'), ((32, 33), 'tlc_superfine'),
            ((38, 39), 'tlc_coarse'), ((36, 37), 'tlc_fine'), ((34, 35), 'tlc_superfine'),
            ((40, 41), 'tlc_coarse'), ((38, 39), 'tlc_fine'), ((36, 37), 'tlc_superfine'),
            ((42, 43), 'tlc_coarse'), ((40, 41), 'tlc_fine'), ((38, 39), 'tlc_superfine'),
            ((44, 45), 'tlc_coarse'), ((42, 43), 'tlc_fine'), ((40, 41), 'tlc_superfine'),
            ((46, 47), 'tlc_coarse'), ((44, 45), 'tlc_fine'), ((42, 43), 'tlc_superfine'),
            ((48, 49), 'tlc_coarse'), ((46, 47), 'tlc_fine'), ((44, 45), 'tlc_superfine'),
            ((50, 51), 'tlc_coarse'), ((48, 49), 'tlc_fine'), ((46, 47), 'tlc_superfine'),
            ((52, 53), 'tlc_coarse'), ((50, 51), 'tlc_fine'), ((48, 49), 'tlc_superfine'),
            ((54, 55), 'tlc_coarse'), ((52, 53), 'tlc_fine'), ((50, 51), 'tlc_superfine'),
            ((56, 57), 'tlc_coarse'), ((54, 55), 'tlc_fine'), ((52, 53), 'tlc_superfine'),
            ((58, 59), 'tlc_coarse'), ((56, 57), 'tlc_fine'), ((54, 55), 'tlc_superfine'),
            ((60, 61), 'tlc_coarse'), ((58, 59), 'tlc_fine'), ((56, 57), 'tlc_superfine'),
            ((62, 63), 'tlc_coarse'), ((60, 61), 'tlc_fine'), ((58, 59), 'tlc_superfine'),
            ((64, 65), 'tlc_coarse'), ((62, 63), 'tlc_fine'), ((60, 61), 'tlc_superfine'),
            ((66, 67), 'tlc_coarse'), ((64, 65), 'tlc_fine'), ((62, 63), 'tlc_superfine'),
            ((68, 69), 'tlc_coarse'), ((66, 67), 'tlc_fine'), ((64, 65), 'tlc_superfine'),
            ((70, 71), 'tlc_coarse'), ((68, 69), 'tlc_fine'), ((66, 67), 'tlc_superfine'),
            ((72, 73), 'tlc_coarse'), ((70, 71), 'tlc_fine'), ((68, 69), 'tlc_superfine'),
            ((74, 75), 'tlc_coarse'), ((72, 73), 'tlc_fine'), ((70, 71), 'tlc_superfine'),
            ((76, 77), 'tlc_coarse'), ((74, 75), 'tlc_fine'), ((72, 73), 'tlc_superfine'),
            ((78, 79), 'tlc_coarse'), ((76, 77), 'tlc_fine'), ((74, 75), 'tlc_superfine'),
            ((80, 81), 'tlc_coarse'), ((78, 79), 'tlc_fine'), ((76, 77), 'tlc_superfine'),
            ((82, 83), 'tlc_coarse'), ((80, 81), 'tlc_fine'), ((78, 79), 'tlc_superfine'),
            ((84, 85), 'tlc_coarse'), ((82, 83), 'tlc_fine'), ((80, 81), 'tlc_superfine'),
            ((86, 87), 'tlc_coarse'), ((84, 85), 'tlc_fine'), ((82, 83), 'tlc_superfine'),
            ((88, 89), 'tlc_coarse'), ((86, 87), 'tlc_fine'), ((84, 85), 'tlc_superfine'),
            ((90, 91), 'tlc_coarse'), ((88, 89), 'tlc_fine'), ((86, 87), 'tlc_superfine'),
            ((92, 93), 'tlc_coarse'), ((90, 91), 'tlc_fine'), ((88, 89), 'tlc_superfine'),
            ((94, 95), 'tlc_coarse'), ((92, 93), 'tlc_fine'), ((90, 91), 'tlc_superfine'),
            ((96, 97), 'tlc_coarse'), ((94, 95), 'tlc_fine'), ((92, 93), 'tlc_superfine'),
            ((98, 99), 'tlc_coarse'), ((96, 97), 'tlc_fine'), ((94, 95), 'tlc_superfine'),
            ((100, 101), 'tlc_coarse'), ((98, 99), 'tlc_fine'), ((96, 97), 'tlc_superfine'),
            ((102, 103), 'tlc_coarse'), ((100, 101), 'tlc_fine'), ((98, 99), 'tlc_superfine'),
            ((104, 105), 'tlc_coarse'), ((102, 103), 'tlc_fine'), ((100, 101), 'tlc_superfine'),
            ((106, 107), 'tlc_coarse'), ((104, 105), 'tlc_fine'), ((102, 103), 'tlc_superfine'),
            ((108, 109), 'tlc_coarse'), ((106, 107), 'tlc_fine'), ((104, 105), 'tlc_superfine'),
            ((110, 111), 'tlc_coarse'), ((108, 109), 'tlc_fine'), ((106, 107), 'tlc_superfine'),
            ((112, 113), 'tlc_coarse'), ((110, 111), 'tlc_fine'), ((108, 109), 'tlc_superfine'),
            ((114, 115), 'tlc_coarse'), ((112, 113), 'tlc_fine'), ((110, 111), 'tlc_superfine'),
            ((116, 117), 'tlc_coarse'), ((114, 115), 'tlc_fine'), ((112, 113), 'tlc_superfine'),
            ((118, 119), 'tlc_coarse'), ((116, 117), 'tlc_fine'), ((114, 115), 'tlc_superfine'),
            ((120, 121), 'tlc_coarse'), ((118, 119), 'tlc_fine'), ((116, 117), 'tlc_superfine'),
            ((122, 123), 'tlc_coarse'), ((120, 121), 'tlc_fine'), ((118, 119), 'tlc_superfine'),
            ((124, 125), 'tlc_coarse'), ((122, 123), 'tlc_fine'), ((120, 121), 'tlc_superfine'),
            ((126, 127), 'tlc_coarse'), ((124, 125), 'tlc_fine'), ((122, 123), 'tlc_superfine'),
            ((128, 129), 'tlc_coarse'), ((126, 127), 'tlc_fine'), ((124, 125), 'tlc_superfine'),
            ((130, 131), 'tlc_coarse'), ((128, 129), 'tlc_fine'), ((126, 127), 'tlc_superfine'),
            ((132, 133), 'tlc_coarse'), ((130, 131), 'tlc_fine'), ((128, 129), 'tlc_superfine'),
            ((134, 135), 'tlc_coarse'), ((132, 133), 'tlc_fine'), ((130, 131), 'tlc_superfine'),
            ((136, 137), 'tlc_coarse'), ((134, 135), 'tlc_fine'), ((132, 133), 'tlc_superfine'),
            ((138, 139), 'tlc_coarse'), ((136, 137), 'tlc_fine'), ((134, 135), 'tlc_superfine'),
            ((140, 141), 'tlc_coarse'), ((138, 139), 'tlc_fine'), ((136, 137), 'tlc_superfine'),
            ((142, 143), 'tlc_coarse'), ((140, 141), 'tlc_fine'), ((138, 139), 'tlc_superfine'),
            ((144, 145), 'tlc_coarse'), ((142, 143), 'tlc_fine'), ((140, 141), 'tlc_superfine'),
            ((146, 147), 'tlc_coarse'), ((144, 145), 'tlc_fine'), ((142, 143), 'tlc_superfine'),
            ((148, 149), 'tlc_coarse'), ((146, 147), 'tlc_fine'), ((144, 145), 'tlc_superfine'),
            ((150, 151), 'tlc_coarse'), ((148, 149), 'tlc_fine'), ((146, 147), 'tlc_superfine'),
            ((152, 153), 'tlc_coarse'), ((150, 151), 'tlc_fine'), ((148, 149), 'tlc_superfine'),
            ((154, 155), 'tlc_coarse'), ((152, 153), 'tlc_fine'), ((150, 151), 'tlc_superfine'),
            ((156, 157), 'tlc_coarse'), ((154, 155), 'tlc_fine'), ((152, 153), 'tlc_superfine'),
            ((158, 159), 'tlc_coarse'), ((156, 157), 'tlc_fine'), ((154, 155), 'tlc_superfine'),
            ((160, 161), 'tlc_coarse'), ((158, 159), 'tlc_fine'), ((156, 157), 'tlc_superfine'),
            ((162, 163), 'tlc_coarse'), ((160, 161), 'tlc_fine'), ((158, 159), 'tlc_superfine'),
            ((164, 165), 'tlc_coarse'), ((162, 163), 'tlc_fine'), ((160, 161), 'tlc_superfine'),
            ((166, 167), 'tlc_coarse'), ((164, 165), 'tlc_fine'), ((162, 163), 'tlc_superfine'),
            ((168, 169), 'tlc_coarse'), ((166, 167), 'tlc_fine'), ((164, 165), 'tlc_superfine'),
            ((170, 171), 'tlc_coarse'), ((168, 169), 'tlc_fine'), ((166, 167), 'tlc_superfine'),
            ((172, 173), 'tlc_coarse'), ((170, 171), 'tlc_fine'), ((168, 169), 'tlc_superfine'),
            ((174, 175), 'tlc_coarse'), ((172, 173), 'tlc_fine'), ((170, 171), 'tlc_superfine'),
            ((176, 177), 'tlc_coarse'), ((174, 175), 'tlc_fine'), ((172, 173), 'tlc_superfine'),
            ((178, 179), 'tlc_coarse'), ((176, 177), 'tlc_fine'), ((174, 175), 'tlc_superfine'),
            ((180, 181), 'tlc_coarse'), ((178, 179), 'tlc_fine'), ((176, 177), 'tlc_superfine'),
            ((182, 183), 'tlc_coarse'), ((180, 181), 'tlc_fine'), ((178, 179), 'tlc_superfine'),
            ((184, 185), 'tlc_coarse'), ((182, 183), 'tlc_fine'), ((180, 181), 'tlc_superfine'),
            ((186, 187), 'tlc_coarse'), ((184, 185), 'tlc_fine'), ((182, 183), 'tlc_superfine'),
            ((188, 189), 'tlc_coarse'), ((186, 187), 'tlc_fine'), ((184, 185), 'tlc_superfine'),
            ((190, 191), 'tlc_coarse'), ((188, 189), 'tlc_fine'), ((186, 187), 'tlc_superfine'),
            ((192, 193), 'tlc_coarse'), ((190, 191), 'tlc_fine'), ((188, 189), 'tlc_superfine'),
            ((194, 195), 'tlc_coarse'), ((192, 193), 'tlc_fine'), ((190, 191), 'tlc_superfine'),
            ((196, 197), 'tlc_coarse'), ((194, 195), 'tlc_fine'), ((192, 193), 'tlc_superfine'),
            ((198, 199), 'tlc_coarse'), ((196, 197), 'tlc_fine'), ((194, 195), 'tlc_superfine'),
            ((200, 201), 'tlc_coarse'), ((198, 199), 'tlc_fine'), ((196, 197), 'tlc_superfine'),
            ((202, 203), 'tlc_coarse'), ((200, 201), 'tlc_fine'), ((198, 199), 'tlc_superfine'),
            ((204, 205), 'tlc_coarse'), ((202, 203), 'tlc_fine'), ((200, 201), 'tlc_superfine'),
            ((206, 207), 'tlc_coarse'), ((204, 205), 'tlc_fine'), ((202, 203), 'tlc_superfine'),
            ((208, 209), 'tlc_coarse'), ((206, 207), 'tlc_fine'), ((204, 205), 'tlc_superfine'),
            ((210, 211), 'tlc_coarse'), ((208, 209), 'tlc_fine'), ((206, 207), 'tlc_superfine'),
            ((212, 213), 'tlc_coarse'), ((210, 211), 'tlc_fine'), ((208, 209), 'tlc_superfine'),
            ((214, 215), 'tlc_coarse'), ((212, 213), 'tlc_fine'), ((210, 211), 'tlc_superfine'),
            ((216, 217), 'tlc_coarse'), ((214, 215), 'tlc_fine'), ((212, 213), 'tlc_superfine'),
            ((218, 219), 'tlc_coarse'), ((216, 217), 'tlc_fine'), ((214, 215), 'tlc_superfine'),
            ((220, 221), 'tlc_coarse'), ((218, 219), 'tlc_fine'), ((216, 217), 'tlc_superfine'),
            ((222, 223), 'tlc_coarse'), ((220, 221), 'tlc_fine'), ((218, 219), 'tlc_superfine'),
            ((224, 225), 'tlc_coarse'), ((222, 223), 'tlc_fine'), ((220, 221), 'tlc_superfine'),
            ((226, 227), 'tlc_coarse'), ((224, 225), 'tlc_fine'), ((222, 223), 'tlc_superfine'),
            ((228, 229), 'tlc_coarse'), ((226, 227), 'tlc_fine'), ((224, 225), 'tlc_superfine'),
            ((230, 231), 'tlc_coarse'), ((228, 229), 'tlc_fine'), ((226, 227), 'tlc_superfine'),
            ((232, 233), 'tlc_coarse'), ((230, 231), 'tlc_fine'), ((228, 229), 'tlc_superfine'),
            ((234, 235), 'tlc_coarse'), ((232, 233), 'tlc_fine'), ((230, 231), 'tlc_superfine'),
            ((236, 237), 'tlc_coarse'), ((234, 235), 'tlc_fine'), ((232, 233), 'tlc_superfine'),
            ((238, 239), 'tlc_coarse'), ((236, 237), 'tlc_fine'), ((234, 235), 'tlc_superfine'),
            ((240, 241), 'tlc_coarse'), ((238, 239), 'tlc_fine'), ((236, 237), 'tlc_superfine'),
            ((242, 243), 'tlc_coarse'), ((240, 241), 'tlc_fine'), ((238, 239), 'tlc_superfine'),
            ((244, 245), 'tlc_coarse'), ((242, 243), 'tlc_fine'), ((240, 241), 'tlc_superfine'),
            ((246, 247), 'tlc_coarse'), ((244, 245), 'tlc_fine'), ((242, 243), 'tlc_superfine'),
            ((248, 249), 'tlc_coarse'), ((246, 247), 'tlc_fine'), ((244, 245), 'tlc_superfine'),
            ((250, 251), 'tlc_coarse'), ((248, 249), 'tlc_fine'), ((246, 247), 'tlc_superfine'),
            ((252, 253), 'slc'), ((250, 251), 'tlc_fine'), ((248, 249, 250, 251), 'tlc_superfine'),
        )


