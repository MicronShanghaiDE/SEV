import re
import dm3
import sys
import time
import types
from Util.decorator import method_tracer
from Util.assertion import Assertion
from Backend.nand_b95a import B95a

class SSD(Assertion):
    def __init__(self, ssd_id = None, serial_number = None, driver_type = None):
        self.drive_list = {}
        self._gather_drive_list()

        while ssd_id is None:
            if serial_number is None:
                for port in self.drive_list.keys():
                    for drive in self.drive_list[port]:
                        print "Port %d, Model %s, SN %s, Capacity %s" % (drive.Port, drive.ModelNumber, drive.SerialNumber, drive.CapacityAsString)
                print "Enter q to exit"

                ssd_id = raw_input("Select the drive to run: ")
                if ssd_id == "q":
                    self.assert_failed("User exit")

                ssd_id = int(ssd_id)
                if ssd_id not in self.drive_list.keys():
                    print "No drive connected to the selected port, please select again"
                    ssd_id = None
            else:  # serial number is not None
                for port in self.drive_list.keys():
                    for drive in self.drive_list[port]:
                        if drive.SerialNumber.strip() == serial_number:
                            ssd_id = drive.Port
                if ssd_id is None:
                    print "No specific serial number found, select again"

        self.drive_id = ssd_id
        self.port_id = self.drive_id + 1
        # dm3.DriverType.OS, dm3.DriverType.DM or dm3.DriverType.MP
        self.driver_type = driver_type
        self.device = None
        self._connect()

        idf = self.IdentifyDevice()
        print "Product is %s" % idf.Model
        print "Firmware is %s" % idf.FirmwareVersion
        print "Serial number is %s" % idf.SerialNumber
        print "Total number of user addressable logical sectors for write/read commands is %d\n" % idf.TotalLbas

        self.nand = B95a(self)

    def __del__(self):
        self._disconnect()
        return self

    def __str__(self):
        return self.__class__.__name__

    def _disconnect(self):
        self.device = None
        return self

    def _gather_drive_list(self):
        self.drive_list = {}
        drive_list = dm3.GetDriveInfoList()
        for drive in drive_list:
            if drive.Capacity != 0:
                if drive.Port in self.drive_list.keys():
                    self.drive_list[drive.Port].append(drive)
                else:
                    self.drive_list[drive.Port] = [drive]
        return

    def _connect_by_drive_id(self):
        self.assert_true(self.drive_id is not None)
        self.assert_true(self.port_id is not None)

        while self.drive_id not in self.drive_list.keys():
            print "No drive attached to user select drive id, select drive again"
            for port in self.drive_list.keys():
                for drive in self.drive_list[port]:
                    print "Port %d, Model %s, SN %s, Capacity %s" % (drive.Port, drive.ModelNumber, drive.SerialNumber, drive.CapacityAsString)
            print "Enter q to exit"

            ssd_id = raw_input("Select the drive to run: ")
            if ssd_id == "q":
                self.assert_failed("User exit")
            self.drive_id = int(ssd_id)

        if len(self.drive_list[self.drive_id]) > 1:
            idx = 0
            for drive in self.drive_list[self.drive_id]:
                print "Index %d, Port %d, Model %s, SN %s, Capacity %s" % (idx, drive.Port, drive.ModelNumber, drive.SerialNumber, drive.CapacityAsString)
                idx += 1
            index = raw_input("Select which drive to run: ")
            index = int(index)
            if index >= len(self.drive_list[self.drive_id]):
                self.assert_failed("Wrong index")
            else:
                drive = self.drive_list[self.drive_id][index]
        else:
            drive = self.drive_list[self.drive_id][0]

        if self.driver_type == "mp":
            self.device = dm3.sata.SataDevice(driveInfo = drive, powerChannel = self.port_id, driverType = dm3.DriverType.MP)
        elif self.driver_type == "os":
            self.device = dm3.sata.SataDevice(driveInfo = drive, powerChannel = self.port_id, driverType = dm3.DriverType.OS)
        elif self.driver_type == "dm":
            self.device = dm3.sata.SataDevice(driveInfo = drive, powerChannel = self.port_id, driverType = dm3.DriverType.DM)
        else:
            self.device = dm3.sata.SataDevice(driveInfo = drive, powerChannel = self.port_id)
        
        self.assert_not_equal(self.device, None, 'Device connection fail by SataDevice(%d)' % self.drive_id)
        if self._serial_id is None:
            self._serial_id = self.IdentifyDevice().SerialNumber

        return self

    def _connect(self):
        '''Only to be used for 1st time connection
        '''
        # self.assert_true(self._serial_id is not None or self.drive_id is not None)
        self.assert_true(self.device is None)

        # Prioritize to use drive number for 1st connection
        if self.drive_id is not None:
            self._connect_by_drive_id()
        from ssd_arch import SSDArch
        self._arch = SSDArch.arch(self.product_familiy_id() + 'Arch')(self)
        self.assert_not_equal(self._arch, None)

        return self

    def product_familiy_id(self):
        model = self.IdentifyDevice().Model.replace(' ', '')
        if model == "EK471HSRM":
            return "Maui"
        elif re.search('BX200SSD', model):
            return "BX200"
        else:
            return None

    def firmware_id(self):
        return self.IdentifyDevice().FirmwareVersion.replace(' ', '')

    def _reconnect(self, idle_time):
        self.assert_true(self.device is not None)
        self._disconnect()

        for i in xrange(0, idle_time, 5):
            try:
                print "Attempt to connect drive id %d..." % self.drive_id
                return self._connect_by_drive_id()
            except:
                print sys.exc_info()[0], sys.exc_info()[1]
                self.wait(5)

        self.assert_failed('connect timeout')

    def _trace_command_error(self, status):
        pass

    def __getitem__(self, key):
        return getattr(self._arch, key)

    def __getattr__(self, name):
        if name.startswith('exec_'):
            command = name[5:]

            def _mixin(self, *args, **kwargs):
                try:
                    response = getattr(self, command)(*args, **kwargs)
                except dm3.AtaCommandError as e:
                    self._trace_command_error(e)
                    raise e

                return response
            _mixin.__name__ = name

            setattr(self, name, types.MethodType(method_tracer()(_mixin), self))
        else:
            '''The code below could not direclty use getattr(self.device, name) to setattr, b/c device object will be changed after power cycle
            '''
            setattr(self, name, lambda *args, **kwargs: getattr(self.device, name)(*args, **kwargs))

        return getattr(self, name)

    @method_tracer()
    def exec_powerOn(self, idle_time = 30):
        """ Power on the drive and wait idle_time afterwards to allow drive to enumerate """
        self.assert_true(isinstance(self.port_id, int))

        pc = dm3.PowerController(self.port_id)
        pc.On()

        return self.wait(idle_time)

    @method_tracer()
    def exec_powerOff(self, idle_time = 0):
        """ Power off the drive and wait idle_time for PLI (< 1 sec, so wait time should be a non-issue) """
        self.assert_true(isinstance(self.port_id, int))

        pc = dm3.PowerController(self.port_id)
        pc.Off()

        return self.wait(idle_time)

    @method_tracer()
    def exec_powerCycle(self, time_out = None, sleep_seconds = 5, should_reconnect = False):
        """ Power cycle the drive, waiting sleep_seconds before powering on,
            and waiting time_out seconds before aborting connection
        """
        self.assert_true(isinstance(self.port_id, int))

        if time_out is None:
            time_out = self['power_cycle_limit']

        pc = dm3.PowerController(self.port_id)
        pc.Off()
        self.wait(sleep_seconds)
        pc.On()

        if should_reconnect:
            return self._reconnect(time_out)
        else:
            return self.wait(sleep_seconds)

    @method_tracer()
    def exec_comReset(self):
        return self.hbaport().ComReset()

    @method_tracer()
    def wait(self, seconds):
        time.sleep(seconds)
        return self

    def max_lba(self):
        return self.max_address_ext()

    @method_tracer(name_only = True)
    def max_address_ext(self):
        return self.IdentifyDevice().TotalLbas

    def hbaport(self):
        from hbaport import HbaPort
        return HbaPort(self).hbaport

    def security(self):
        from security import Security
        return Security(self).security

    def ncq(self):
        from ncq import Ncq
        return Ncq(self).ncq

    def smart(self):
        from smart import Smart
        return Smart(self).smart


