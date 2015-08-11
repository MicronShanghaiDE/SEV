import unittest
import random
import sys

class DutTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super(unittest.TextTestResult, self).startTest(test)

        self.stream.writeln(self.separator1)
        self.stream.write(self.getDescription(test))
        self.stream.writeln(" ... ")
        self.stream.writeln(self.separator2)
        self.stream.flush()

    def addSuccess(self, test):
        super(unittest.TextTestResult, self).addSuccess(test)
        self.stream.writeln("ok")

    def addError(self, test, err):
        super(unittest.TextTestResult, self).addError(test, err)
        self.stream.writeln("ERROR %s" % self.errors[-1][1])

    def addFailure(self, test, err):
        super(unittest.TextTestResult, self).addFailure(test, err)
        self.stream.writeln("FAIL %s" % self.failures[-1][1])

    def addSkip(self, test, reason):
        super(unittest.TextTestResult, self).addSkip(test, reason)
        self.stream.writeln("skipped {0!r}".format(reason))

    def addExpectedFailure(self, test, err):
        super(unittest.TextTestResult, self).addExpectedFailure(test, err)
        self.stream.writeln("expected failure")

    def addUnexpectedSuccess(self, test):
        super(unittest.TextTestResult, self).addUnexpectedSuccess(test)
        self.stream.writeln("unexpected success")

    def printErrors(self):
        self.stream.writeln()

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour, self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)

_dut_args = None

def _dut_run_pyunit_test_once(test_cls):
    statuses = []

    global _dut_args

    runner = unittest.TextTestRunner(sys.stdout, verbosity = 0, resultclass = DutTestResult)

    if _dut_args.test_case is None or _dut_args.test_case == 'all' or sys.argv[0].endswith('\\' + _dut_args.test_case):
        test_result = unittest.main(argv = sys.argv[:1], testRunner = runner, exit = False).result
        statuses.append(test_result.wasSuccessful())
    else:
        for test_case in _dut_args.test_case.split(";"):
            if test_cls is None:
                import inspect
                # Use first found test class defined in the main module as test_cls
                module = __import__('__main__')
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and\
                       hasattr(obj, test_case) and inspect.getfile(obj) == sys.argv[0]:
                        test_cls = obj
                        break

            test_result = runner.run(test_cls(test_case))
            statuses.append(test_result.wasSuccessful())

    if all(statuses):
        print "PyUnit Test Passed"
    else:
        print "PyUnit Test Failed"

    return all(statuses)

def dut_run_pyunit_test(test_cls = None, extended_arguments = None):
    '''Execute PyUnit test
    if test_case is specified: execute test_cls.test_case
    else: execute all test* in test_cls
    '''
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--drive-id', type = int)
    parser.add_argument('-s', '--serial-id', type = str)
    parser.add_argument('-t', '--test-case', type = str)
    parser.add_argument('-l', '--loop', type = int)
    parser.add_argument('-seed', '--seed', type = long)
    parser.add_argument('-dt', '--driver-type', type = str)

    if extended_arguments is not None:
        extended_arguments(parser)

    global _dut_args
    _dut_args = parser.parse_args()

    if _dut_args.seed is None:
        import time
        _dut_args.seed = long(time.time() * 256)

    if _dut_args.loop is None or _dut_args.loop == 1:
        status = _dut_run_pyunit_test_once(test_cls)
    else:
        statuses = []
        for i in xrange(_dut_args.loop):
            print "Loop", i

            statuses.append(_dut_run_pyunit_test_once(test_cls))

        status = all(statuses)

    if status:
        exit(0)
    else:
        exit(-1)

def dut_args():
    global _dut_args
    return _dut_args

def dut_setup_ssd(test_case):
    global _dut_args

    print "Test", sys.argv[0], _dut_args
    print "Random seed:", _dut_args.seed
    print

    random.seed(_dut_args.seed)

    from DUT.ssd import SSD

    return SSD(ssd_id = _dut_args.drive_id, serial_number = _dut_args.serial_id, driver_type = _dut_args.driver_type)

def dut_teardown_device(device):
    device.__del__()

