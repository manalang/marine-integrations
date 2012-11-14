"""
@package mi.instrument.seabird.sbe54tps.ooicore.driver
@file /Users/unwin/OOI/Workspace/code/marine-integrations/mi/instrument/seabird/sbe54tps/ooicore/driver.py
@author Roger Unwin
@brief Driver for the ooicore
Release notes:

10.180.80.170:2101 Instrument
10.180.80.170:2102 Digi
Done
"""

__author__ = 'Roger Unwin'
__license__ = 'Apache 2.0'

import string
import re

from mi.core.common import BaseEnum
from mi.core.instrument.instrument_protocol import CommandResponseInstrumentProtocol
from mi.core.instrument.instrument_fsm import InstrumentFSM
from mi.core.instrument.instrument_driver import SingleConnectionInstrumentDriver
from mi.core.instrument.instrument_driver import DriverEvent
from mi.core.instrument.instrument_driver import DriverAsyncEvent
from mi.core.instrument.instrument_driver import DriverProtocolState
from mi.core.instrument.instrument_driver import DriverParameter

from mi.core.log import get_logger ; log = get_logger()

from mi.core.instrument.data_particle import DataParticle, DataParticleKey, DataParticleValue
# newline.
NEWLINE = '\r\n'

# default timeout.
TIMEOUT = 10

STATUS_DATA_REGEX = r"(<StatusData DeviceType='.*?</StatusData>)"
STATUS_DATA_REGEX_MATCHER = re.compile(STATUS_DATA_REGEX, re.DOTALL)

CONFIGURATION_DATA_REGEX = r"(<ConfigurationData DeviceType=.*?</ConfigurationData>)"
CONFIGURATION_DATA_REGEX_MATCHER = re.compile(CONFIGURATION_DATA_REGEX, re.DOTALL)

EVENT_COUNTER_DATA_REGEX = r"(<EventSummary numEvents='.*?</EventList>)"
EVENT_COUNTER_DATA_REGEX_MATCHER = re.compile(EVENT_COUNTER_DATA_REGEX, re.DOTALL)

HARDWARE_DATA_REGEX = r"(<HardwareData DeviceType='.*?</HardwareData>)"
HARDWARE_DATA_REGEX_MATCHER = re.compile(HARDWARE_DATA_REGEX, re.DOTALL)

SAMPLE_DATA_REGEX = r"<Sample Num='.*?</Sample>"
SAMPLE_DATA_REGEX_MATCHER = re.compile(SAMPLE_DATA_REGEX, re.DOTALL)






# Packet config
STREAM_NAME_PARSED = DataParticleValue.PARSED
STREAM_NAME_RAW = DataParticleValue.RAW
PACKET_CONFIG = [STREAM_NAME_PARSED, STREAM_NAME_RAW]

PACKET_CONFIG = {
    STREAM_NAME_PARSED : 'ctd_parsed_param_dict',
    STREAM_NAME_RAW : 'ctd_raw_param_dict'
}



# Device specific parameters.
class InstrumentCmds(BaseEnum):
    """
    Instrument Commands
    These are the commands that according to the science profile must be supported.
    """


    #### Artificial Constructed Commands for Driver ####
    SET = "set"  # need to bring over _build_set_command/_parse_set_response
    #GET = "get"

    ################
    #### Status ####
    ################
    GET_CONFIGURATION_DATA = "GetCD"
    GET_STATUS_DATA = "GetSD"
    GET_EVENT_COUNTER_DATA = "GetEC"
    GET_HARDWARE_DATA = "GetHD"

    ###############################
    #### Setup - Communication ####
    ###############################
    # SET_BAUD_RATE = "SetBaudRate"                                         # DO NOT IMPLEMENT

    #########################
    #### Setup - General ####
    #########################
    # INITIALIZE = "*Init"                                                  # DO NOT IMPLEMENT
    SET_SAMPLE_PERIOD = "SetSamplePeriod"                  # VARIABLE
    SET_TIME = "SetTime"                                   # VARIABLE       # S>settime=2006-01-15T13:31:00
    SET_BATTERY_TYPE = "SetBatteryType"                    # VARIABLE

    ###########################
    #### Setup Data Output ####
    ###########################
    SET_ENABLE_ALERTS ="SetEnableAlerts"                   # VARIABLE

    ##################
    #### Sampling ####
    ##################
    INIT_LOGGING = "InitLogging"
    START_SAMPLING = "Start"
    STOP_SAMPLING = "Stop"
    SAMPLE_REFERENCE_OSCILLATOR = "SampleRefOsc"

    ################################
    #### Data Access and Upload ####
    ################################
    # GET_SAMPLES = "GetSamples"                                            # DO NOT IMPLEMENT
    # GET_LAST_PRESSURE_SAMPLES = "GetLastPSamples"                         # DO NOT IMPLEMENT
    # GET_LAST_REFERENCE_SAMPLES = "GetLastRSamples"                        # DO NOT IMPLEMENT
    # GET_REFERENCE_SAMPLES_LIST = "GetRSampleList"                         # DO NOT IMPLEMENT
    SET_UPLOAD_TYPE = "SetUploadType"                      # VARIABLE
    # UPLOAD_DATA = "UploadData"                                            # DO NOT IMPLEMENT

    ####################
    #### Diagnostic ####
    ####################
    RESET_EC = "ResetEC"
    TEST_EPROM = "TestEeprom"
    # TEST_REFERENCE_OSCILLATOR = "TestRefOsc"                              # DO NOT IMPLEMENT

    ##################################
    #### Calibration Coefficients ####
    ##################################
    # SetAcqOscCalDate=S        S= acquisition crystal calibration date.
    # SET_ACQUISITION_OSCILLATOR_CALIBRATION_DATE = "SetAcqOscCalDate"      # DO NOT IMPLEMENT

    # SetFRA0=F                 F= acquisition crystal frequency A0.
    # SET_ACQUISITION_FREQUENCY_A0 = "SetFRA0"                              # DO NOT IMPLEMENT

    # SetFRA1=F                 F= acquisition crystal frequency A1.
    # SET_ACQUISITION_FREQUENCY_A1 = "SetFRA1"                              # DO NOT IMPLEMENT

    # SetFRA2=F                 F= acquisition crystal frequency A2.
    # SET_ACQUISITION_FREQUENCY_A2 = "SetFRA2"                              # DO NOT IMPLEMENT

    # SetFRA3=F                 F= acquisition crystal frequency A3.
    # SET_ACQUISITION_FREQUENCY_A3 = "SetFRA3"                              # DO NOT IMPLEMENT

    # SetPressureCalDate=S      S= pressure sensor calibration date.
    # SET_PRESSURE_CALIBRATION_DATE = "SetPressureCalDate"                  # DO NOT IMPLEMENT

    # SetPressureSerialNum=S    S= pressure sensor serial number.
    # SET_PRESSURE_SERIAL_NUMBER = "SetPressureSerialNum"                   # DO NOT IMPLEMENT

    # SetPRange=F               F= pressure sensor full scale range (psia).
    # SET_PRESSURE_SENSOR_FULL_SCALE_RANGE = "SetPRange"                    # DO NOT IMPLEMENT

    # SetPOffset=F              F= pressure sensor offset (psia).
    # SET_PRESSURE_SENSOR_OFFSET = "SetPOffset"                             # DO NOT IMPLEMENT

    # SetPU0=F                  F= pressure sensor U0.
    # SET_PRESSURE_SENSOR_U0 = "SetPU0"                                     # DO NOT IMPLEMENT

    # SetPY1=F                  F= pressure sensor Y1.
    # SET_PRESSURE_SENSOR_Y1 = "SetPY1"                                     # DO NOT IMPLEMENT

    # SetPY2=F                  F= pressure sensor Y2.
    # SET_PRESSURE_SENSOR_Y2 = "SetPY2"                                     # DO NOT IMPLEMENT

    # SetPY3=F                  F= pressure sensor Y3.
    # SET_PRESSURE_SENSOR_Y3 = "SetPY3"                                     # DO NOT IMPLEMENT

    # SetPC1=F                  F= pressure sensor C1.
    # SET_PRESSURE_SENSOR_C1 = "SetPC1"                                     # DO NOT IMPLEMENT

    # SetPC2=F                  F= pressure sensor C2.
    # SET_PRESSURE_SENSOR_C2 = "SetPC2"                                     # DO NOT IMPLEMENT

    # SetPC3=F                  F= pressure sensor C3.
    # SET_PRESSURE_SENSOR_C3 = "SetPC3"                                     # DO NOT IMPLEMENT

    # SetPD1=F                  F= pressure sensor D1.
    # SET_PRESSURE_SENSOR_D1 = "SetPD1"                                     # DO NOT IMPLEMENT

    # SetPD2=F                  F= pressure sensor D2.
    # SET_PRESSURE_SENSOR_D2 = "SetPD2"                                     # DO NOT IMPLEMENT

    # SetPT1=F                  F= pressure sensor T1.
    # SET_PRESSURE_SENSOR_T1 = "SetPT1"                                     # DO NOT IMPLEMENT

    # SetPT2=F                  F= pressure sensor T2.
    # SET_PRESSURE_SENSOR_T2 = "SetPT2"                                     # DO NOT IMPLEMENT

    # SetPT3=F                  F= pressure sensor T3.
    # SET_PRESSURE_SENSOR_T3 = "SetPT3"                                     # DO NOT IMPLEMENT

    # SetPT4=F                  F= pressure sensor T4.
    # SET_PRESSURE_SENSOR_T4 = "SetPT4"                                     # DO NOT IMPLEMENT



# Device specific parameters.
class Parameter(DriverParameter):
    """
    Device parameters
    """
    BATTERY_TYPE = "BatteryType"        # SetBatteryType
    BAUD_RATE = "BaudRate"              # SetBaudRate
    TIME = "Time"                       # SetTime
    ENABLE_ALERTS = "EnableAlerts"      # SetEnableAlerts
    UPLOAD_TYPE = "UploadType"          # SetUploadType
    SAMPLE_PERIOD = "SamplePeriod"      # SetSamplePeriod

    # Calibration Parameters
    # ACQUISITION_OSCILLATOR_CALIBRATION_DATE = "AcqOscCalDate" # S
    # ACQUISITION_FREQUENCY_A0 = "FRA0" # F
    # ACQUISITION_FREQUENCY_A1 = "FRA1" # F
    # ACQUISITION_FREQUENCY_A2 = "FRA2" # F
    # ACQUISITION_FREQUENCY_A3 = "FRA3" # F
    # PRESSURE_CALIBRATION_DATE = "PressureCalDate" # S
    # PRESSURE_SERIAL_NUMBER = "PressureSerialNum" # S
    # PRESSURE_SENSOR_FULL_SCALE_RANGE = "prange"     # F # (psia)
    # PRESSURE_SENSOR_OFFSET = "poffset"              # F # (psia)
    #
    # PRESSURE_SENSOR_U0 = "pu0" # F
    # PRESSURE_SENSOR_Y1 = "py1" # F
    # PRESSURE_SENSOR_Y2 = "py2" # F
    # PRESSURE_SENSOR_Y3 = "py3" # F
    # PRESSURE_SENSOR_C1 = "pc1" # F
    # PRESSURE_SENSOR_C2 = "pc2" # F
    # PRESSURE_SENSOR_C3 = "pc3" # F
    # PRESSURE_SENSOR_D1 = "pd1" # F
    # PRESSURE_SENSOR_D2 = "pd2" # F
    # PRESSURE_SENSOR_T1 = "pt1" # F
    # PRESSURE_SENSOR_T2 = "pt2" # F
    # PRESSURE_SENSOR_T3 = "pt3" # F
    # PRESSURE_SENSOR_T4 = "pt4" # F



class ProtocolState(BaseEnum):
    """
    Protocol states
    enum.
    """
    UNKNOWN = DriverProtocolState.UNKNOWN
    COMMAND = DriverProtocolState.COMMAND
    AUTOSAMPLE = DriverProtocolState.AUTOSAMPLE
    DIRECT_ACCESS = DriverProtocolState.DIRECT_ACCESS
    #TEST = DriverProtocolState.TEST
    #CALIBRATE = DriverProtocolState.CALIBRATE


class ProtocolEvent(BaseEnum):
    """
    Protocol events
    """
    FORCE_STATE = DriverEvent.FORCE_STATE

    ENTER = DriverEvent.ENTER
    EXIT = DriverEvent.EXIT
    START_DIRECT = DriverEvent.START_DIRECT
    STOP_DIRECT = DriverEvent.STOP_DIRECT
    EXECUTE_DIRECT = DriverEvent.EXECUTE_DIRECT

    DISCOVER = DriverEvent.DISCOVER
    START_AUTOSAMPLE = DriverEvent.START_AUTOSAMPLE
    STOP_AUTOSAMPLE = DriverEvent.STOP_AUTOSAMPLE

    CLOCK_SYNC = DriverEvent.CLOCK_SYNC

    ACQUIRE_SAMPLE = DriverEvent.ACQUIRE_SAMPLE
    ACQUIRE_STATUS = DriverEvent.ACQUIRE_STATUS

    INIT_LOGGING = 'PROTOCOL_EVENT_INIT_LOGGING'

    # Do we need these here?
    GET = DriverEvent.GET
    SET = DriverEvent.SET

    PING_DRIVER = DriverEvent.PING_DRIVER





######################################### PARTICLES #############################


class SBE54tpsStatusDataParticleKey(BaseEnum):
    DEVICE_TYPE = "device_type"
    SERIAL_NUMBER = "serial_number"
    DATE_TIME = "date_time"
    EVENT_COUNT = "event_count"
    MAIN_SUPPLY_VOLTAGE = "main_supply_voltage"
    NUMBER_OF_SAMPLES = "number_of_samples"
    BYTES_USED = "bytes_used"
    BYTES_FREE = "bytes_free"

class SBE54tpsStatusDataParticle(DataParticle):
    """
    Routines for parsing raw data into a data particle structure. Override
    the building of values, and the rest should come along for free.
    """
    def _build_parsed_values(self):
        """
        Take something in the StatusData format and split it into
        values with appropriate tags

        @throws SampleException If there is a problem with sample creation
        """

        single_var_matchers  = {
            SBE54tpsStatusDataParticleKey.DEVICE_TYPE:
                re.compile(r"StatusData DeviceType='([^']+'"),
            SBE54tpsStatusDataParticleKey.SERIAL_NUMBER:
                re.compile(r"SerialNumber='(\d+)'"),
            SBE54tpsStatusDataParticleKey.DATE_TIME:
                re.compile(r"<DateTime>([^<]+)</DateTime>"),
            SBE54tpsStatusDataParticleKey.EVENT_COUNT:
                re.compile(r"<EventSummary numEvents='(\d+)'/>"),
            SBE54tpsStatusDataParticleKey.MAIN_SUPPLY_VOLTAGE:
                re.compile(r"<MainSupplyVoltage>(\d+)</MainSupplyVoltage>"),
            SBE54tpsStatusDataParticleKey.NUMBER_OF_SAMPLES:
                re.compile(r"<Samples>(\d+)</Samples>"),
            SBE54tpsStatusDataParticleKey.BYTES_USED:
                re.compile(r"<Bytes>(\d+)</Bytes>"),
            SBE54tpsStatusDataParticleKey.BYTES_FREE:
                re.compile(r"<BytesFree>(\d+)</BytesFree>")
        }

        # Initialize

        single_var_matches  = {
            SBE54tpsStatusDataParticleKey.DEVICE_TYPE: None,
            SBE54tpsStatusDataParticleKey.SERIAL_NUMBER: None,
            SBE54tpsStatusDataParticleKey.DATE_TIME: None,
            SBE54tpsStatusDataParticleKey.EVENT_COUNT: None,
            SBE54tpsStatusDataParticleKey.MAIN_SUPPLY_VOLTAGE: None,
            SBE54tpsStatusDataParticleKey.NUMBER_OF_SAMPLES: None,
            SBE54tpsStatusDataParticleKey.BYTES_USED: None,
            SBE54tpsStatusDataParticleKey.BYTES_FREE: None
        }

        for line in self.raw_data.split(NEWLINE):
            for (key, matcher) in single_var_matchers:
                match = single_var_matchers[key].match(line)
                if match:

                    # str
                    if key in [
                        SBE54tpsStatusDataParticleKey.DEVICE_TYPE
                    ]:
                        single_var_matches[key] = match(1)

                    # int
                    elif key in [
                        SBE54tpsStatusDataParticleKey.SERIAL_NUMBER,
                        SBE54tpsStatusDataParticleKey.EVENT_COUNT,
                        SBE54tpsStatusDataParticleKey.NUMBER_OF_SAMPLES,
                        SBE54tpsStatusDataParticleKey.BYTES_USED,
                        SBE54tpsStatusDataParticleKey.BYTES_FREE
                    ]:
                        single_var_matches[key] = int(match(1))

                    #float
                    elif key in [
                        SBE54tpsStatusDataParticleKey.MAIN_SUPPLY_VOLTAGE
                    ]:
                        single_var_matches[key] = float(match(1))

                    # datetime
                    elif key in [
                        SBE54tpsStatusDataParticleKey.DATE_TIME
                    ]:
                        # 2012-11-13T17:56:42
                        # yyyy-mm-ddThh:mm:ss
                        text_timestamp = match(1)
                        py_timestamp = time.strptime(text_timestamp, "%Y-%m-%dT%H:%M:%S")
                        timestamp = ntplib.system_to_ntp_time(time.mktime(py_timestamp))
                        single_var_matches[key] = timestamp

                    else:
                        raise SampleException("Unknown variable type in SBE54tpsStatusDataParticle._build_parsed_values")

        result = []
        for (key, value) in single_var_matches:
            result.append({DataParticleKey.VALUE_ID: key,
                           DataParticleKey.VALUE: value})

        return result

class SBE54tpsConfigurationDataParticleKey(BaseEnum):
    DEVICE_TYPE = "device_type"
    SERIAL_NUMBER = "serial_number"
    ACQ_OSC_CAL_DATE = "acquisition_crystal_calibration_date"
    FRA0 = "fra0"
    FRA1 = "fra1"
    FRA2 = "fra2"
    FRA3 = "fra3"
    PRESSURE_SERIAL_NUM = "pressure_serial_number"
    PRESSURE_CAL_DATE = "pressure_calibration_date"
    PU0 = "pu0"
    PY1 = "py1"
    PY2 = "py2"
    PY3 = "py3"
    PC1 = "pc1"
    PC2 = "pc2"
    PC3 = "pc3"
    PD1 = "pd1"
    PD2 = "pd2"
    PT1 = "pt1"
    PT2 = "pt2"
    PT3 = "pt3"
    PT4 = "pt4"
    PRESSURE_OFFSET = "pressure_sensor_offset" # pisa
    PRESSURE_RANGE = "pressure_sensor_full_scale_range" # pisa
    BATTERY_TYPE = "battery_type"
    BAUD_RATE = "baud_rate"
    ENABLE_ALERTS = "enable_alerts"
    UPLOAD_TYPE = "upload_type"
    SAMPLE_PERIOD = "sample_period"

class SBE54tpsConfigurationDataParticle(DataParticle):
    """
    Routines for parsing raw data into a data particle structure. Override
    the building of values, and the rest should come along for free.
    """
    def _build_parsed_values(self):
        """
        Take something in the StatusData format and split it into
        values with appropriate tags

        @throws SampleException If there is a problem with sample creation
        """


        single_var_matchers  = {
            SBE54tpsConfigurationDataParticleKey.DEVICE_TYPE:
                re.compile(r"ConfigurationData DeviceType='([^']+)' "),
            SBE54tpsConfigurationDataParticleKey.SERIAL_NUMBER:
                re.compile(r" SerialNumber='(\d+)'>"),
            SBE54tpsConfigurationDataParticleKey.ACQ_OSC_CAL_DATE:
                re.compile(r"<AcqOscCalDate>([0-9\-]+)</AcqOscCalDate>"),
            SBE54tpsConfigurationDataParticleKey.FRA0:
                re.compile(r"<FRA0>([0-9E+-.]+)</FRA0>"),
            SBE54tpsConfigurationDataParticleKey.FRA1:
                re.compile(r"<FRA1>([0-9E+-.]+)</FRA1>"),
            SBE54tpsConfigurationDataParticleKey.FRA2:
                re.compile(r"<FRA2>([0-9E+-.]+)</FRA2>"),
            SBE54tpsConfigurationDataParticleKey.FRA3:
                re.compile(r"<FRA3>([0-9E+-.]+)</FRA3>"),
            SBE54tpsConfigurationDataParticleKey.PRESSURE_SERIAL_NUM:
                re.compile(r"<PressureSerialNum>(\d+)</PressureSerialNum>"),
            SBE54tpsConfigurationDataParticleKey.PRESSURE_CAL_DATE:
                re.compile(r"<PressureCalDate>([0-9\-]+)</PressureCalDate>"),
            SBE54tpsConfigurationDataParticleKey.PU0:
                re.compile(r"<pu0>([0-9E+-.]+)</pu0>"),
            SBE54tpsConfigurationDataParticleKey.PY1:
                re.compile(r"<py1>([0-9E+-.]+)</py1>"),
            SBE54tpsConfigurationDataParticleKey.PY2:
                re.compile(r"<py2>([0-9E+-.]+)</py2>"),
            SBE54tpsConfigurationDataParticleKey.PY3:
                re.compile(r"<py3>([0-9E+-.]+)</py3>"),
            SBE54tpsConfigurationDataParticleKey.PC1:
                re.compile(r"<pc1>([0-9E+-.]+)</pc1>"),
            SBE54tpsConfigurationDataParticleKey.PC2:
                re.compile(r"<pc2>([0-9E+-.]+)</pc2>"),
            SBE54tpsConfigurationDataParticleKey.PC3:
                re.compile(r"<pc3>([0-9E+-.]+)</pc3>"),
            SBE54tpsConfigurationDataParticleKey.PD1:
                re.compile(r"<pd1>([0-9E+-.]+)</pd1>"),
            SBE54tpsConfigurationDataParticleKey.PD2:
                re.compile(r"<pd2>([0-9E+-.]+)</pd2>"),
            SBE54tpsConfigurationDataParticleKey.PT1:
                re.compile(r"<pt1>([0-9E+-.]+)</pt1>"),
            SBE54tpsConfigurationDataParticleKey.PT2:
                re.compile(r"<pt2>([0-9E+-.]+)</pt2>"),
            SBE54tpsConfigurationDataParticleKey.PT3:
                re.compile(r"<pt3>([0-9E+-.]+)</pt3>"),
            SBE54tpsConfigurationDataParticleKey.PT4:
                re.compile(r"<pt4>([0-9E+-.]+)</pt4>"),
            SBE54tpsConfigurationDataParticleKey.PRESSURE_OFFSET:
                re.compile(r"<poffset>([0-9E+-.]+)</poffset>"),
            SBE54tpsConfigurationDataParticleKey.PRESSURE_RANGE:
                re.compile(r"<prange>([0-9E+-.]+)</prange>"),
            SBE54tpsConfigurationDataParticleKey.BATTERY_TYPE:
                re.compile(r"batteryType='(\d+)'"),
            SBE54tpsConfigurationDataParticleKey.BAUD_RATE:
                re.compile(r"baudRate='(\d+)'"),
            SBE54tpsConfigurationDataParticleKey.ENABLE_ALERTS:
                re.compile(r"enableAlerts='(\d+)'"),
            SBE54tpsConfigurationDataParticleKey.UPLOAD_TYPE:
                re.compile(r"uploadType='(\d+)'"),
            SBE54tpsConfigurationDataParticleKey.SAMPLE_PERIOD:
                re.compile(r"samplePeriod='(\d+)'")
        }

        # Initialize

        single_var_matches  = {
            SBE54tpsConfigurationDataParticleKey.DEVICE_TYPE: None,
            SBE54tpsConfigurationDataParticleKey.SERIAL_NUMBER: None,
            SBE54tpsConfigurationDataParticleKey.ACQ_OSC_CAL_DATE: None,
            SBE54tpsConfigurationDataParticleKey.FRA0: None,
            SBE54tpsConfigurationDataParticleKey.FRA1: None,
            SBE54tpsConfigurationDataParticleKey.FRA2: None,
            SBE54tpsConfigurationDataParticleKey.FRA3: None,
            SBE54tpsConfigurationDataParticleKey.PRESSURE_SERIAL_NUM: None,
            SBE54tpsConfigurationDataParticleKey.PRESSURE_CAL_DATE: None,
            SBE54tpsConfigurationDataParticleKey.PU0: None,
            SBE54tpsConfigurationDataParticleKey.PY1: None,
            SBE54tpsConfigurationDataParticleKey.PY2: None,
            SBE54tpsConfigurationDataParticleKey.PY3: None,
            SBE54tpsConfigurationDataParticleKey.PC1: None,
            SBE54tpsConfigurationDataParticleKey.PC2: None,
            SBE54tpsConfigurationDataParticleKey.PC3: None,
            SBE54tpsConfigurationDataParticleKey.PD1: None,
            SBE54tpsConfigurationDataParticleKey.PD2: None,
            SBE54tpsConfigurationDataParticleKey.PT1: None,
            SBE54tpsConfigurationDataParticleKey.PT2: None,
            SBE54tpsConfigurationDataParticleKey.PT3: None,
            SBE54tpsConfigurationDataParticleKey.PT4: None,
            SBE54tpsConfigurationDataParticleKey.PRESSURE_OFFSET: None,
            SBE54tpsConfigurationDataParticleKey.PRESSURE_RANGE: None,
            SBE54tpsConfigurationDataParticleKey.BATTERY_TYPE: None,
            SBE54tpsConfigurationDataParticleKey.BAUD_RATE: None,
            SBE54tpsConfigurationDataParticleKey.ENABLE_ALERTS: None,
            SBE54tpsConfigurationDataParticleKey.UPLOAD_TYPE: None,
            SBE54tpsConfigurationDataParticleKey.SAMPLE_PERIOD: None
        }

        for line in self.raw_data.split(NEWLINE):
            for (key, matcher) in single_var_matchers:
                match = single_var_matchers[key].match(line)
                if match:

                    # str
                    if key in [
                        SBE54tpsConfigurationDataParticleKey.DEVICE_TYPE,
                        SBE54tpsConfigurationDataParticleKey.PRESSURE_SERIAL_NUM,
                    ]:
                        single_var_matches[key] = match(1)

                    # int
                    elif key in [
                        SBE54tpsConfigurationDataParticleKey.SERIAL_NUMBER,
                        SBE54tpsConfigurationDataParticleKey.BATTERY_TYPE,
                        SBE54tpsConfigurationDataParticleKey.ENABLE_ALERTS,
                        SBE54tpsConfigurationDataParticleKey.UPLOAD_TYPE,
                        SBE54tpsConfigurationDataParticleKey.SAMPLE_PERIOD
                    ]:
                        single_var_matches[key] = int(match(1))

                    #float
                    elif key in [
                        SBE54tpsConfigurationDataParticleKey.FRA0,
                        SBE54tpsConfigurationDataParticleKey.FRA1,
                        SBE54tpsConfigurationDataParticleKey.FRA2,
                        SBE54tpsConfigurationDataParticleKey.FRA3,
                        SBE54tpsConfigurationDataParticleKey.PU0,
                        SBE54tpsConfigurationDataParticleKey.PY1,
                        SBE54tpsConfigurationDataParticleKey.PY2,
                        SBE54tpsConfigurationDataParticleKey.PY3,
                        SBE54tpsConfigurationDataParticleKey.PC1,
                        SBE54tpsConfigurationDataParticleKey.PC2,
                        SBE54tpsConfigurationDataParticleKey.PC3,
                        SBE54tpsConfigurationDataParticleKey.PD1,
                        SBE54tpsConfigurationDataParticleKey.PD2,
                        SBE54tpsConfigurationDataParticleKey.PT1,
                        SBE54tpsConfigurationDataParticleKey.PT2,
                        SBE54tpsConfigurationDataParticleKey.PT3,
                        SBE54tpsConfigurationDataParticleKey.PT4,
                        SBE54tpsConfigurationDataParticleKey.PRESSURE_OFFSET,
                        SBE54tpsConfigurationDataParticleKey.PRESSURE_RANGE
                    ]:
                        single_var_matches[key] = float(match(1))

                    # date
                    elif key in [
                        SBE54tpsConfigurationDataParticleKey.ACQ_OSC_CAL_DATE,
                        SBE54tpsConfigurationDataParticleKey.PRESSURE_CAL_DATE
                    ]:
                        # ISO8601-2000 format.
                        # yyyy-mm-dd
                        # 2007-03-01
                        text_timestamp = match(1)
                        py_timestamp = time.strptime(text_timestamp, "%Y-%m-%d")
                        timestamp = ntplib.system_to_ntp_time(time.mktime(py_timestamp))
                        single_var_matches[key] = timestamp

                    else:
                        raise SampleException("Unknown variable type in SBE54tpsConfigurationDataParticle._build_parsed_values")

        result = []
        for (key, value) in single_var_matches:
            result.append({DataParticleKey.VALUE_ID: key,
                           DataParticleKey.VALUE: value})

        return result

class SBE54tpsEventCounterDataParticleKey(BaseEnum):
    NUMBER_EVENTS = "number_events"
    MAX_STACK = "max_stack"
    DEVICE_TYPE = "device_type"
    SERIAL_NUMBER = "serial_number"
    POWER_ON_RESET = "power_on_reset"
    POWER_FAIL_RESET = "power_fail_reset"
    SERIAL_BYTE_ERROR = "serial_byte_error"
    COMMAND_BUFFER_OVERFLOW = "command_buffer_overflow"
    SERIAL_RECEIVE_OVERFLOW = "serial_receive_overflow"
    LOW_BATTERY = "low_battery"
    SIGNAL_ERROR = "signal_error"
    ERROR_10 = "error_10"
    ERROR_12 = "error_12"

class SBE54tpsEventCounterDataParticle(DataParticle):
    """
    Routines for parsing raw data into a data particle structure. Override
    the building of values, and the rest should come along for free.
    """
    def _build_parsed_values(self):
        """
        Take something in the StatusData format and split it into
        values with appropriate tags

        @throws SampleException If there is a problem with sample creation
        """

        single_var_matchers  = {
            SBE54tpsEventCounterDataParticleKey.NUMBER_EVENTS:
                re.compile(r"EventSummary numEvents='(\d+)' "),
            SBE54tpsEventCounterDataParticleKey.MAX_STACK:
                re.compile(r" maxStack='(\d+)'/>"),
            SBE54tpsEventCounterDataParticleKey.DEVICE_TYPE:
                re.compile(r"<EventList DeviceType='([^']+)' "),
            SBE54tpsEventCounterDataParticleKey.SERIAL_NUMBER:
                re.compile(r" SerialNumber='(\d+)'>"),
            SBE54tpsEventCounterDataParticleKey.POWER_ON_RESET:
                re.compile(r"<Event type='PowerOnReset' count='(\d+)'/>"),
            SBE54tpsEventCounterDataParticleKey.POWER_FAIL_RESET:
                re.compile(r"<Event type='PowerFailReset' count='(\d+)'/>"),
            SBE54tpsEventCounterDataParticleKey.SERIAL_BYTE_ERROR:
                re.compile(r"<Event type='SerialByteErr' count='(\d+)'/>"),
            SBE54tpsEventCounterDataParticleKey.COMMAND_BUFFER_OVERFLOW:
                re.compile(r"<Event type='CMDBuffOflow' count='(\d+)'/>"),
            SBE54tpsEventCounterDataParticleKey.SERIAL_RECEIVE_OVERFLOW:
                re.compile(r"<Event type='SerialRxOflow' count='(\d+)'/>"),
            SBE54tpsEventCounterDataParticleKey.LOW_BATTERY:
                re.compile(r"<Event type='LowBattery' count='(\d+)'/>"),
            SBE54tpsEventCounterDataParticleKey.SIGNAL_ERROR:
                re.compile(r"<Event type='SignalErr' count='(\d+)'/>"),
            SBE54tpsEventCounterDataParticleKey.ERROR_10:
                re.compile(r"<Event type='Error10' count='(\d+)'/>"),
            SBE54tpsEventCounterDataParticleKey.ERROR_12:
                re.compile(r"<Event type='Error12' count='(\d+)'/>")
        }


        # Initialize

        single_var_matches  = {
            SBE54tpsEventCounterDataParticleKey.NUMBER_EVENTS: None,
            SBE54tpsEventCounterDataParticleKey.MAX_STACK: None,
            SBE54tpsEventCounterDataParticleKey.DEVICE_TYPE: None,
            SBE54tpsEventCounterDataParticleKey.SERIAL_NUMBER: None,
            SBE54tpsEventCounterDataParticleKey.POWER_ON_RESET: None,
            SBE54tpsEventCounterDataParticleKey.POWER_FAIL_RESET: None,
            SBE54tpsEventCounterDataParticleKey.SERIAL_BYTE_ERROR: None,
            SBE54tpsEventCounterDataParticleKey.COMMAND_BUFFER_OVERFLOW: None,
            SBE54tpsEventCounterDataParticleKey.SERIAL_RECEIVE_OVERFLOW: None,
            SBE54tpsEventCounterDataParticleKey.LOW_BATTERY: None,
            SBE54tpsEventCounterDataParticleKey.SIGNAL_ERROR: None,
            SBE54tpsEventCounterDataParticleKey.ERROR_10: None,
            SBE54tpsEventCounterDataParticleKey.ERROR_12: None
        }

        for line in self.raw_data.split(NEWLINE):
            for (key, matcher) in single_var_matchers:
                match = single_var_matchers[key].match(line)
                if match:
                    # int
                    if key in [
                        SBE54tpsEventCounterDataParticleKey.NUMBER_EVENTS,
                        SBE54tpsEventCounterDataParticleKey.MAX_STACK,
                        SBE54tpsEventCounterDataParticleKey.DEVICE_TYPE,
                        SBE54tpsEventCounterDataParticleKey.SERIAL_NUMBER,
                        SBE54tpsEventCounterDataParticleKey.POWER_ON_RESET,
                        SBE54tpsEventCounterDataParticleKey.POWER_FAIL_RESET,
                        SBE54tpsEventCounterDataParticleKey.SERIAL_BYTE_ERROR,
                        SBE54tpsEventCounterDataParticleKey.COMMAND_BUFFER_OVERFLOW,
                        SBE54tpsEventCounterDataParticleKey.SERIAL_RECEIVE_OVERFLOW,
                        SBE54tpsEventCounterDataParticleKey.LOW_BATTERY,
                        SBE54tpsEventCounterDataParticleKey.SIGNAL_ERROR,
                        SBE54tpsEventCounterDataParticleKey.ERROR_10,
                        SBE54tpsEventCounterDataParticleKey.ERROR_12
                    ]:
                        single_var_matches[key] = int(match(1))
                    else:
                        raise SampleException("Unknown variable type in SBE54tpsEventCounterDataParticle._build_parsed_values")

        result = []
        for (key, value) in single_var_matches:
            result.append({DataParticleKey.VALUE_ID: key,
                           DataParticleKey.VALUE: value})

        return result

class SBE54tpsHardwareDataParticleKey(BaseEnum):
    DEVICE_TYPE = "device_type"
    SERIAL_NUMBER = "serial_number"
    MANUFACTURER = "manufacturer"
    FIRMWARE_VERSION = "firmware_version"
    FIRMWARE_DATE = "firmware_date"
    HARDWARE_VERSION = "hardware_version"
    PCB_SERIAL_NUMBER = "pcb_serial_number"
    PCB_TYPE = "pcb_type"
    MANUFACTUR_DATE = "manufactur_date"

class SBE54tpsHardwareDataParticle(DataParticle):
    """
    Routines for parsing raw data into a data particle structure. Override
    the building of values, and the rest should come along for free.
    """
    def _build_parsed_values(self):
        """
        Take something in the StatusData format and split it into
        values with appropriate tags

        @throws SampleException If there is a problem with sample creation
        """

        single_var_matchers  = {
            SBE54tpsHardwareDataParticleKey.DEVICE_TYPE:
                re.compile(r"<HardwareData DeviceType='[^']+' "),
            SBE54tpsHardwareDataParticleKey.SERIAL_NUMBER:
                re.compile(r" SerialNumber='(\d+)'>"),
            SBE54tpsHardwareDataParticleKey.MANUFACTURER:
                re.compile(r"<Manufacturer>([^<]+)</Manufacturer>"),
            SBE54tpsHardwareDataParticleKey.FIRMWARE_VERSION:
                re.compile(r"<FirmwareVersion>([^<]+)</FirmwareVersion>"),
            SBE54tpsHardwareDataParticleKey.FIRMWARE_DATE:
                re.compile(r"<FirmwareDate>([^<]+)</FirmwareDate>"),
            SBE54tpsHardwareDataParticleKey.HARDWARE_VERSION:
                re.compile(r"<HardwareVersion>([^<]+)</HardwareVersion>"),
            SBE54tpsHardwareDataParticleKey.PCB_SERIAL_NUMBER:
                re.compile(r"<PCBSerialNum>([^<]+)</PCBSerialNum>"),
            SBE54tpsHardwareDataParticleKey.PCB_TYPE:
                re.compile(r"<PCBType>([^<]+)</PCBType>"),
            SBE54tpsHardwareDataParticleKey.MANUFACTUR_DATE:
                re.compile(r"<MfgDate>([^<]+)</MfgDate>")
        }

        # Initialize
        single_var_matches  = {
            SBE54tpsHardwareDataParticleKey.DEVICE_TYPE: None,
            SBE54tpsHardwareDataParticleKey.SERIAL_NUMBER: None,
            SBE54tpsHardwareDataParticleKey.MANUFACTURER: None,
            SBE54tpsHardwareDataParticleKey.FIRMWARE_VERSION: None,
            SBE54tpsHardwareDataParticleKey.FIRMWARE_DATE: None,
            SBE54tpsHardwareDataParticleKey.HARDWARE_VERSION: [],
            SBE54tpsHardwareDataParticleKey.PCB_SERIAL_NUMBER: [],
            SBE54tpsHardwareDataParticleKey.PCB_TYPE: None,
            SBE54tpsHardwareDataParticleKey.MANUFACTUR_DATE: None
        }

        for line in self.raw_data.split(NEWLINE):
            for (key, matcher) in single_var_matchers:
                match = single_var_matchers[key].match(line)
                if match:

                    # str
                    if key in [
                        SBE54tpsHardwareDataParticleKey.DEVICE_TYPE,
                        SBE54tpsHardwareDataParticleKey.MANUFACTURER,
                        SBE54tpsHardwareDataParticleKey.FIRMWARE_VERSION,
                        SBE54tpsHardwareDataParticleKey.HARDWARE_VERSION,
                        SBE54tpsHardwareDataParticleKey.PCB_SERIAL_NUMBER,
                        SBE54tpsHardwareDataParticleKey.PCB_TYPE
                    ]:
                        if single_var_matches[key] != None:
                            single_var_matches[key].append(match(1))
                        else:
                            single_var_matches[key] = match(1)

                    # int
                    elif key in [
                        SBE54tpsHardwareDataParticleKey.SERIAL_NUMBER
                    ]:
                        single_var_matches[key] = int(match(1))

                    # date
                    elif key in [
                        SBE54tpsHardwareDataParticleKey.FIRMWARE_DATE,
                        SBE54tpsHardwareDataParticleKey.MANUFACTUR_DATE
                    ]:
                        # <FirmwareDate>Mar 22 2007</FirmwareDate>
                        # <MfgDate>Jun 27 2007</MfgDate>
                        text_timestamp = match(1)
                        py_timestamp = time.strptime(text_timestamp, "%b %d %Y")
                        timestamp = ntplib.system_to_ntp_time(time.mktime(py_timestamp))
                        single_var_matches[key] = timestamp

                    else:
                        raise SampleException("Unknown variable type in SBE54tpsConfigurationDataParticle._build_parsed_values")

        result = []
        for (key, value) in single_var_matches:
            result.append({DataParticleKey.VALUE_ID: key,
                           DataParticleKey.VALUE: value})

        return result

class SBE54tpsSampleDataParticleKey(BaseEnum):
    SAMPLE_NUMBER = "sample_number"
    SAMPLE_TYPE = "sample_type"
    SAMPLE_TIMESTAMP = "sample_timestamp"
    PRESSURE = "pressure" # psi
    PRESSURE_TEMP = "pressure_temp"

class SBE54tpsSampleDataParticle(DataParticle):
    """
    Routines for parsing raw data into a data particle structure. Override
    the building of values, and the rest should come along for free.
    """
    def _build_parsed_values(self):
        """
        Take something in the StatusData format and split it into
        values with appropriate tags

        @throws SampleException If there is a problem with sample creation
        """

        single_var_matchers  = {
            SBE54tpsSampleDataParticleKey.SAMPLE_NUMBER:
                re.compile(r"<Sample Num='(\d+)' "),
            SBE54tpsSampleDataParticleKey.SAMPLE_TYPE:
                re.compile(r" Type='([^']+)'>"),
            SBE54tpsSampleDataParticleKey.SAMPLE_TIMESTAMP:
                re.compile(r"<Time>([^<]+)</Time>"),
            SBE54tpsSampleDataParticleKey.PRESSURE:
                re.compile(r"<PressurePSI>([0-9.+-]+)</PressurePSI>"),
            SBE54tpsSampleDataParticleKey.PRESSURE_TEMP:
                re.compile(r"<PTemp>([0-9.+-]+)</PTemp>")
        }

        # Initialize
        single_var_matches  = {
            SBE54tpsSampleDataParticleKey.SAMPLE_NUMBER: None,
            SBE54tpsSampleDataParticleKey.SAMPLE_TYPE: None,
            SBE54tpsSampleDataParticleKey.SAMPLE_TIMESTAMP: None,
            SBE54tpsSampleDataParticleKey.PRESSURE: None,
            SBE54tpsSampleDataParticleKey.PRESSURE_TEMP: None
        }

        for line in self.raw_data.split(NEWLINE):
            for (key, matcher) in single_var_matchers:
                match = single_var_matchers[key].match(line)
                if match:

                    # str
                    if key in [
                        SBE54tpsSampleDataParticleKey.SAMPLE_TYPE
                    ]:
                        if single_var_matches[key] != None:
                            single_var_matches[key].append(match(1))
                        else:
                            single_var_matches[key] = match(1)

                    # int
                    elif key in [
                        SBE54tpsSampleDataParticleKey.SAMPLE_NUMBER
                    ]:
                        single_var_matches[key] = int(match(1))

                    # float
                    elif key in [
                        SBE54tpsSampleDataParticleKey.PRESSURE,
                        SBE54tpsSampleDataParticleKey.PRESSURE_TEMP
                    ]:
                        single_var_matches[key] = float(match(1))

                    # date_time
                    elif key in [
                        SBE54tpsSampleDataParticleKey.SAMPLE_TIMESTAMP
                    ]:
                        # <Time>2012-11-07T12:21:25</Time>
                        # yyyy-mm-ddThh:mm:ss
                        text_timestamp = match(1)
                        py_timestamp = time.strptime(text_timestamp, "%Y-%m-%dT%H:%M:%S")
                        timestamp = ntplib.system_to_ntp_time(time.mktime(py_timestamp))
                        single_var_matches[key] = timestamp

                    else:
                        raise SampleException("Unknown variable type in SBE54tpsConfigurationDataParticle._build_parsed_values")

        result = []
        for (key, value) in single_var_matches:
            result.append({DataParticleKey.VALUE_ID: key,
                           DataParticleKey.VALUE: value})

        return result




######################################### /PARTICLES #############################

# Device prompts.
class Prompt(BaseEnum):
    """
    io prompts.
    """
    COMMAND = "<Executed/>\r\nS>"

    AUTOSAMPLE = "<Executed/>\r\n"

    BAD_COMMAND_AUTOSAMPLE = "<Error.*?\r\n<Executed/>\r\n" # REGEX ALERT
    BAD_COMMAND = "<Error.*?\r\n<Executed/>\r\nS>" # REGEX ALERT

###############################################################################
# Driver
###############################################################################

class InstrumentDriver(SingleConnectionInstrumentDriver):
    """
    InstrumentDriver subclass
    Subclasses SingleConnectionInstrumentDriver with connection state
    machine.
    """
    def __init__(self, evt_callback):
        """
        Driver constructor.
        @param evt_callback Driver process event callback.
        """
        #Construct superclass.
        SingleConnectionInstrumentDriver.__init__(self, evt_callback)

    ########################################################################
    # Superclass overrides for resource query.
    ########################################################################

    def get_resource_params(self):
        """
        Return list of device parameters available.
        """
        return Parameter.list()

    ########################################################################
    # Protocol builder.
    ########################################################################

    def _build_protocol(self):
        """
        Construct the driver protocol state machine.
        """
        self._protocol = Protocol(Prompt, NEWLINE, self._driver_event)

###############################################################################
# Protocol
################################################################################

class Protocol(CommandResponseInstrumentProtocol):
    """
    Instrument protocol class
    Subclasses CommandResponseInstrumentProtocol
    """
    def __init__(self, prompts, newline, driver_event):
        """
        Protocol constructor.
        @param prompts A BaseEnum class containing instrument prompts.
        @param newline The newline.
        @param driver_event Driver process event callback.
        """
        # Construct protocol superclass.
        CommandResponseInstrumentProtocol.__init__(self, prompts, newline, driver_event)

        # Build protocol state machine.
        self._protocol_fsm = InstrumentFSM(ProtocolState, ProtocolEvent,
            ProtocolEvent.ENTER, ProtocolEvent.EXIT)

        # Add event handlers for protocol state machine.
        self._protocol_fsm.add_handler(ProtocolState.UNKNOWN, ProtocolEvent.ENTER,                  self._handler_unknown_enter)
        self._protocol_fsm.add_handler(ProtocolState.UNKNOWN, ProtocolEvent.EXIT,                   self._handler_unknown_exit)
        self._protocol_fsm.add_handler(ProtocolState.UNKNOWN, ProtocolEvent.DISCOVER,               self._handler_unknown_discover)
        #self._protocol_fsm.add_handler(ProtocolState.UNKNOWN, ProtocolEvent.START_DIRECT,           self._handler_command_start_direct)  ##???? from unknown state?
        self._protocol_fsm.add_handler(ProtocolState.UNKNOWN, ProtocolEvent.FORCE_STATE,            self._handler_unknown_force_state)   ######

        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.ENTER,                  self._handler_command_enter)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.EXIT,                   self._handler_command_exit)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.ACQUIRE_SAMPLE,         self._handler_command_acquire_sample)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.START_AUTOSAMPLE,       self._handler_command_start_autosample)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.GET,                    self._handler_command_get)  ### ??
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.SET,                    self._handler_command_set)  ### ??

        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.CLOCK_SYNC,             self._handler_command_clock_sync)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.ACQUIRE_STATUS,         self._handler_command_aquire_status)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.START_DIRECT,           self._handler_command_start_direct)

        self._protocol_fsm.add_handler(ProtocolState.AUTOSAMPLE, ProtocolEvent.ENTER,               self._handler_autosample_enter)
        self._protocol_fsm.add_handler(ProtocolState.AUTOSAMPLE, ProtocolEvent.EXIT,                self._handler_autosample_exit)
        self._protocol_fsm.add_handler(ProtocolState.AUTOSAMPLE, ProtocolEvent.GET,                 self._handler_command_get)
        self._protocol_fsm.add_handler(ProtocolState.AUTOSAMPLE, ProtocolEvent.STOP_AUTOSAMPLE,     self._handler_autosample_stop_autosample)

        self._protocol_fsm.add_handler(ProtocolState.DIRECT_ACCESS, ProtocolEvent.ENTER,            self._handler_direct_access_enter)
        self._protocol_fsm.add_handler(ProtocolState.DIRECT_ACCESS, ProtocolEvent.EXIT,             self._handler_direct_access_exit)
        self._protocol_fsm.add_handler(ProtocolState.DIRECT_ACCESS, ProtocolEvent.STOP_DIRECT,      self._handler_direct_access_stop_direct)
        self._protocol_fsm.add_handler(ProtocolState.DIRECT_ACCESS, ProtocolEvent.EXECUTE_DIRECT,   self._handler_direct_access_execute_direct)

        # Construct the parameter dictionary containing device parameters,
        # current parameter values, and set formatting functions.
        self._build_param_dict()

        # Add build handlers for device commands.

        # Add response handlers for device commands.

        # Add sample handlers.

        # State state machine in UNKNOWN state.
        self._protocol_fsm.start(ProtocolState.UNKNOWN)

        # commands sent sent to device to be filtered in responses for telnet DA
        self._sent_cmds = []



    ########################################################################
    # Unknown handlers.
    ########################################################################

    def _handler_unknown_enter(self, *args, **kwargs):
        """
        Enter unknown state.
        """
        # Tell driver superclass to send a state change event.
        # Superclass will query the state.
        self._driver_event(DriverAsyncEvent.STATE_CHANGE)

    def _handler_unknown_force_state(self, *args, **kwargs):
        """
        Force driver into a given state for the purposes of unit testing
        @param state=desired_state Required desired state to transition to.
        @raises InstrumentParameterException if no st'ate parameter.
        """
        log.debug("************* " + repr(kwargs))
        log.debug("************* in _handler_unknown_force_state()" + str(kwargs.get('state', None)))

        state = kwargs.get('state', None)  # via kwargs
        if state is None:
            raise InstrumentParameterException('Missing state parameter.')

        next_state = state
        result = state

        return (next_state, result)

    def _handler_unknown_discover(self, *args, **kwargs):
        """
        Discover current state
        @retval (next_state, result)
        """
        next_state = None
        result = None

        """
        Need to work out what to put in here, likely based by sending a new linbe and analyzing the prompt.
        """


        return (next_state, result)

    def _handler_unknown_exit(self, *args, **kwargs):
        """
        Exit unknown state.
        """
        pass



    ########################################################################
    # Command handlers.
    ########################################################################

    def _handler_command_enter(self, *args, **kwargs):
        """
        Enter command state.
        @throws InstrumentTimeoutException if the device cannot be woken.
        @throws InstrumentProtocolException if the update commands and not recognized.
        """
        # Command device to update parameters and send a config change event.
        #self._update_params()

        # Tell driver superclass to send a state change event.
        # Superclass will query the state.

        self._restore_da_params()
        log.debug("*** IN _handler_command_enter(), updating params")
        self._update_params()

        self._driver_event(DriverAsyncEvent.STATE_CHANGE)

    def _handler_command_acquire_sample(self, *args, **kwargs):
        """
        Acquire sample from SBE54TPS.
        @retval (next_state, result) tuple, (None, sample dict).
        @throws InstrumentTimeoutException if device cannot be woken for command.
        @throws InstrumentProtocolException if command could not be built or misunderstood.
        @throws SampleException if a sample could not be extracted from result.
        """

        next_state = None
        next_agent_state = None
        result = None

        kwargs['timeout'] = 45 # samples can take a long time


        """
        to do aquire sample, will need to:
        stop
        getcd to learn current sampling period
        SetSamplePeriod=1
        collect a sample
        stop
        restore sample period.
        """

        #result = self._do_cmd_resp(InstrumentCmds.TAKE_SAMPLE, *args, **kwargs)

        return (next_state, (next_agent_state, result))

    def _handler_command_aquire_status(self, *args, **kwargs):
        """
        Send a command
        @param args:
        @param kwargs:
        @return:
        """
        next_state = None
        next_agent_state = None
        '''
        GetCD Get and display configuration data.
        GetSD Get and display status data.
        GetEC Get and display event counter data.
        GetHD Get and display hardware data.
        '''

        result = self._do_cmd_resp('ds', *args, **kwargs)

        return (next_state, (next_agent_state, result))

    def _handler_command_start_direct(self):
        """
        """
        next_state = None
        result = None

        next_state = ProtocolState.DIRECT_ACCESS

        return (next_state, result)

    def _handler_command_start_autosample(self, *args, **kwargs):
        """
        Enter autosample mode.
        @retval (next_state, result) tuple, (None, sample dict).
        @throws InstrumentTimeoutException if device cannot be woken for command.
        @throws InstrumentProtocolException if command could not be built or misunderstood.
        @throws SampleException if a sample could not be extracted from result.

        <Executed/>
        S>start
        start
        <Executed/>
        """
        next_state = ProtocolState.AUTOSAMPLE
        next_agent_state = ResourceAgentState.STREAMING

        result = self._do_cmd_resp(InstrumentCmds.START_SAMPLING, *args, **kwargs)

        return (next_state, (next_agent_state, result))

    def _handler_command_get(self, *args, **kwargs):
        """
        Get device parameters from the parameter dict.
        @param args[0] list of parameters to retrieve, or DriverParameter.ALL.
        @throws InstrumentParameterException if missing or invalid parameter.
        """
        next_state = None
        result = None

        # Retrieve the required parameter, raise if not present.
        try:
            params = args[0]

        except IndexError:
            raise InstrumentParameterException('Get command requires a parameter list or tuple.')

        # If all params requested, retrieve config.
        if params == DriverParameter.ALL:
            result = self._param_dict.get_config()

        # If not all params, confirm a list or tuple of params to retrieve.
        # Raise if not a list or tuple.
        # Retireve each key in the list, raise if any are invalid.
        else:
            if not isinstance(params, (list, tuple)):
                raise InstrumentParameterException('Get argument not a list or tuple.')
            result = {}
            for key in params:
                try:
                    val = self._param_dict.get(key)
                    result[key] = val

                except KeyError:
                    raise InstrumentParameterException(('%s is not a valid parameter.' % key))

        return (next_state, result)

    def _handler_command_set(self, *args, **kwargs):
        """
        Perform a set command.
        @param args[0] parameter : value dict.
        @retval (next_state, result) tuple, (None, None).
        @throws InstrumentParameterException if missing set parameters, if set parameters not ALL and
        not a dict, or if paramter can't be properly formatted.
        @throws InstrumentTimeoutException if device cannot be woken for set command.
        @throws InstrumentProtocolException if set command could not be built or misunderstood.
        """
        next_state = None
        result = None

        try:
            params = args[0]
            log.debug("######### params = " + str(repr(params)))

        except IndexError:
            raise InstrumentParameterException('Set command requires a parameter dict.')

        if not isinstance(params, dict):
            raise InstrumentParameterException('Set parameters not a dict.')

        # For each key, val in the dict, issue set command to device.
        # Raise if the command not understood.
        else:
            for (key, val) in params.iteritems():
                log.debug("KEY = " + str(key) + " VALUE = " + str(val))
                result = self._do_cmd_resp(InstrumentCmds.SET, key, val, **kwargs)
                log.debug("**********************RESULT************* = " + str(result))


    def _handler_command_clock_sync(self, *args, **kwargs):
        """
        execute a clock sync on the leading edge of a second change
        @retval (next_state, result) tuple, (ProtocolState.AUTOSAMPLE,
        None) if successful.
        @throws InstrumentTimeoutException if device cannot be woken for command.
        @throws InstrumentProtocolException if command could not be built or misunderstood.
        """

        next_state = None
        next_agent_state = None
        result = None

        timeout = kwargs.get('timeout', TIMEOUT)
        delay = 1
        prompt = self._wakeup(timeout=timeout, delay=delay)

        # lets clear out any past data so it doesnt confuse the command
        self._linebuf = ''
        self._promptbuf = ''

        """
        SetTime=x
        settime=2012-11-13T15:23:18

        ---
        Trying it a bit different from the sbe26
        ---
        """

        timestamp = get_timestamp_delayed("%Y-%b-%dT%H:%M:%S")
        set_cmd = '%s=%s' % (InstrumentCmds.SET_TIME, timestamp) + NEWLINE

        self._do_cmd_direct(set_cmd)
        (prompt, response) = self._get_response() #timeout=30)

        if response != set_cmd + Prompt.COMMAND:
            raise InstrumentProtocolException("_handler_clock_sync - response != set_cmd")

        if prompt != Prompt.COMMAND:
            raise InstrumentProtocolException("_handler_clock_sync - prompt != Prompt.COMMAND")

        return (next_state, (next_agent_state, result))

    def _handler_command_exit(self, *args, **kwargs):
        """
        Exit command state.
        """
        pass

    ########################################################################
    # Direct access handlers.
    ########################################################################

    def _handler_direct_access_enter(self, *args, **kwargs):
        """
        Enter direct access state.
        """
        # Tell driver superclass to send a state change event.
        # Superclass will query the state.
        self._driver_event(DriverAsyncEvent.STATE_CHANGE)

        self._sent_cmds = []

    def _save_da_params(self):
        # Doing the ds command here causes issues.  I think we have to trust the last value that we
        # fetched from a ds/dc


        pd = self._param_dict.get_config()

        self._da_save_dict = {}

        for p in [
            Parameter.SAMPLE_PERIOD,
            Parameter.BATTERY_TYPE,
            Parameter.ENABLE_ALERTS
        ]:
            self._da_save_dict[p] = pd[p]
            log.debug("DIRECT ACCESS PARAM SAVE " + str(p) + " = " + str(self._da_save_dict[p]))

        self._da_save_dict[Parameter.UPLOAD_TYPE] = 0 # Always FORCE to 0 on return from DA
        log.debug("DIRECT ACCESS PARAM SAVE [FORCING] " + str(Parameter.UPLOAD_TYPE) + " = 0")

    def _restore_da_params(self):
        """

        NEEDS TO BE FINISHED



        called from _handler_command_enter, as it behaves poorly
        if caled from _handler_direct_access_exit
        @return:
        """
        run = True
        try:
            if self._da_save_dict == None:
                run = False
        except:
            run = False

        if run == True:
            # clear out the last command.
            self._promptbuf = ''
            self._linebuf = ''

            for k in self._da_save_dict.keys():
                v = self._da_save_dict[k]

                try:
                    str_val = self._param_dict.format(k, v)
                    set_cmd = '%s=%s' % (k, str_val) + NEWLINE
                    log.debug("DIRECT ACCESS PARAM RESTORE " + str(k) + "=" + str_val)
                except KeyError:
                    raise InstrumentParameterException('Unknown driver parameter %s' % param)

                # clear out the last command.
                self._promptbuf = ''
                self._linebuf = ''
                self._do_cmd_direct(set_cmd)

                (prompt, response) = self._get_response(timeout=30)
                while prompt != Prompt.COMMAND:
                    if prompt == Prompt.CONFIRMATION_PROMPT:
                        # clear out the last command.
                        self._promptbuf = ''
                        self._linebuf = ''
                        self._do_cmd_direct("y" + NEWLINE)
                        (prompt, response) = self._get_response(timeout=30)
                    else:
                        (prompt, response) = self._get_response(timeout=30)

            self._da_save_dict = None
            # clear out the last command.
            self._promptbuf = ''
            self._linebuf = ''


    def _handler_direct_access_exit(self, *args, **kwargs):
        """
        Exit direct access state.
        """
        pass

    def _handler_direct_access_execute_direct(self, data):
        """
        """
        next_state = None
        result = None
        next_agent_state = None

        self._do_cmd_direct(data)

        # add sent command to list for 'echo' filtering in callback
        self._sent_cmds.append(data)

        return (next_state, (next_agent_state, result))

    def _handler_direct_access_stop_direct(self):
        """
        @throw InstrumentProtocolException on invalid command
        """

        next_state = None
        result = None

        next_state = ProtocolState.COMMAND
        next_agent_state = ResourceAgentState.COMMAND

        return (next_state, (next_agent_state, result))




    '''

    param_dict  =  [{ParamDict.KEY: key,
     ParamDict.VALUE: value,
     ParamDict.TYPE: type,
     ParamDict.TO_STRING: to_string_lambda,
     ParamDict.FROM_STRING: from_string_lambda},
     {ParamDict.KEY: key,
     ParamDict.VALUE: value,
     ParamDict.TYPE: type,
     ParamDict.TO_STRING: to_string_lambda,
     ParamDict.FROM_STRING: from_string_lambda}]

    The param_dict class would want the following members at minimum:
     pd.define_var(var_name, var_type, to_string_lambda, from_string_lambda)
     pd.set_var_string(var_name, var_value)
     pd.set_var_native(var_name, var_value)
     pd.get_var_string(var_name)
     pd.get_var_native(var_name)

    I suppose we could even extend this further with
     pd.set_var_default_string(var_name, var_default_value)
     pd.set_var_default_native(var_name, var_default_value)

    Then we could set default values per device family in the driver, and perhaps over-ride with device instance vars
     pd.set_var_instance_default_string(var_name, var_instance_default_value)
     pd.set_var_instance_default_native(var_name, var_instance_default_value)
    '''




    def _build_set_command(self, cmd, param, val):
        """
        Build handler for set commands. SETparam=val followed by newline.
        String val constructed by param dict formatting function.  <--- needs a better/clearer way
        @param param the parameter key to set.
        @param val the parameter value to set.
        @ retval The set command to be sent to the device.
        @ retval The set command to be sent to the device.
        @throws InstrumentProtocolException if the parameter is not valid or
        if the formatting function could not accept the value passed.
        """
        try:
            str_val = self._param_dict.format(param, val)
            set_cmd = 'SET%s=%s' % (param, str_val)

            set_cmd = set_cmd + NEWLINE
        except KeyError:
            raise InstrumentParameterException('Unknown driver parameter %s' % param)

        return set_cmd

    def _build_param_dict(self):
        """
        Populate the parameter dictionary with parameters.
        For each parameter key, add match stirng, match lambda function,
        and value formatting function for set commands.
        """
        # Add parameter handlers to parameter dict.

    '''

    This SHOULD be a relic now...

    def got_data(self, data):
        """
        Callback for receiving new data from the device.
        """
        # got data callback for direct access only
        # TODO: should we have a generic got_data in the base class that does something useful??  Is this code
        # TODO: instrument specific?
        if self.get_current_state() == ProtocolState.DIRECT_ACCESS:
            # direct access mode
            if len(data) > 0:
                log.debug("Protocol._got_data(): <" + data + ">")
                # check for echoed commands from instrument (TODO: this should only be done for telnet?)
                if len(self._sent_cmds) > 0:
                    # there are sent commands that need to have there echoes filtered out
                    oldest_sent_cmd = self._sent_cmds[0]
                    if string.count(data, oldest_sent_cmd) > 0:
                        # found a command echo, so remove it from data and delete the command form list
                        data = string.replace(data, oldest_sent_cmd, "", 1)
                        self._sent_cmds.pop(0)
                if len(data) > 0 and self._driver_event:
                    self._driver_event(DriverAsyncEvent.DIRECT_ACCESS, data)
                    # TODO: what about logging this as an event?
            return
    '''

    def _got_chunk(self, chunk):
        """
        The base class got_data has gotten a chunk from the chunker.  Pass it to extract_sample
        with the appropriate particle objects and REGEXes.
        """
        self._extract_sample(SBE54tpsStatusDataParticle, STATUS_DATA_REGEX_MATCHER, chunk)
        self._extract_sample(SBE54tpsConfigurationDataParticle, CONFIGURATION_DATA_REGEX_MATCHER, chunk)
        self._extract_sample(SBE54tpsEventCounterDataParticle, EVENT_COUNTER_DATA_REGEX_MATCHER, chunk)
        self._extract_sample(SBE54tpsHardwareDataParticle, HARDWARE_DATA_REGEX_MATCHER, chunk)
        self._extract_sample(SBE54tpsSampleDataParticle, SAMPLE_DATA_REGEX_MATCHER, chunk)



    def _send_wakeup(self):
        """
        Send a newline to attempt to wake the sbe26plus device.
        """

        self._connection.send(NEWLINE)

    def _build_simple_command(self, cmd):
        """
        Build handler for basic sbe26plus commands.
        @param cmd the simple sbe37 command to format.
        @retval The command to be sent to the device.
        """

        return cmd + NEWLINE
