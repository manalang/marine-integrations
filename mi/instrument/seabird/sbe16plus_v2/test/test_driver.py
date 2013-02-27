"""
@package mi.instrument.seabird.sbe16plus_v2.test.test_driver
@file mi/instrument/seabird/sbe16plus_v2/test/test_driver.py
@author David Everett 
@brief Test cases for InstrumentDriver

USAGE:
 Make tests verbose and provide stdout
   * From the IDK
       $ bin/test_driver
       $ bin/test_driver -u
       $ bin/test_driver -i
       $ bin/test_driver -q

   * From pyon
       $ bin/nosetests -s -v .../mi/instrument/seabird/sbe16plus_v2/ooicore
       $ bin/nosetests -s -v .../mi/instrument/seabird/sbe16plus_v2/ooicore -a UNIT
       $ bin/nosetests -s -v .../mi/instrument/seabird/sbe16plus_v2/ooicore -a INT
       $ bin/nosetests -s -v .../mi/instrument/seabird/sbe16plus_v2/ooicore -a QUAL
"""

__author__ = 'David Everett'
__license__ = 'Apache 2.0'

# Standard lib imports
import time
import unittest

# 3rd party imports
from nose.plugins.attrib import attr
from mock import Mock
from mock import patch
from pyon.core.bootstrap import CFG

# MI logger
from mi.core.log import get_logger ; log = get_logger()

from interface.objects import AgentCommand
from mi.core.common import BaseEnum

from mi.core.instrument.data_particle import DataParticleKey, DataParticleValue

from mi.core.instrument.instrument_driver import DriverAsyncEvent
from mi.core.instrument.instrument_driver import DriverConnectionState
from mi.core.instrument.instrument_driver import DriverProtocolState
from mi.core.instrument.instrument_driver import DriverEvent
from mi.core.instrument.instrument_driver import DriverParameter
from mi.core.instrument.chunker import StringChunker


from mi.idk.unit_test import DriverTestMixin
from mi.idk.unit_test import ParameterTestConfigKey
from mi.idk.unit_test import AgentCapabilityType

from mi.core.exceptions import InstrumentException
from mi.core.exceptions import InstrumentTimeoutException
from mi.core.exceptions import InstrumentParameterException
from mi.core.exceptions import InstrumentStateException
from mi.core.exceptions import InstrumentCommandException

from mi.instrument.seabird.sbe16plus_v2.driver import SBE16Protocol
from mi.instrument.seabird.sbe16plus_v2.driver import SBE16InstrumentDriver
from mi.instrument.seabird.sbe16plus_v2.driver import DataParticleType
from mi.instrument.seabird.sbe16plus_v2.driver import NEWLINE
from mi.instrument.seabird.sbe16plus_v2.driver import SBE16DataParticle, SBE16DataParticleKey
from mi.instrument.seabird.sbe16plus_v2.driver import SBE16StatusParticle, SBE16StatusParticleKey
from mi.instrument.seabird.sbe16plus_v2.driver import SBE16CalibrationParticle, SBE16CalibrationParticleKey
from mi.instrument.seabird.sbe16plus_v2.driver import ProtocolState
from mi.instrument.seabird.sbe16plus_v2.driver import ProtocolEvent
from mi.instrument.seabird.sbe16plus_v2.driver import ScheduledJob
from mi.instrument.seabird.sbe16plus_v2.driver import Capability
from mi.instrument.seabird.sbe16plus_v2.driver import Parameter
from mi.instrument.seabird.sbe16plus_v2.driver import Command
from mi.instrument.seabird.sbe16plus_v2.driver import Prompt

from ion.agents.instrument.direct_access.direct_access_server import DirectAccessTypes

from mi.instrument.seabird.test.test_driver import SeaBirdUnitTest
from mi.instrument.seabird.test.test_driver import SeaBirdIntegrationTest
from mi.instrument.seabird.test.test_driver import SeaBirdQualificationTest
from mi.instrument.seabird.test.test_driver import SeaBirdPublicationTest
from mi.core.instrument.chunker import StringChunker

from pyon.agent.agent import ResourceAgentState
from pyon.agent.agent import ResourceAgentEvent
from pyon.core.exception import Conflict

###
# Test Inputs
###
VALID_SAMPLE = "#0409DB0A738C81747A84AC0006000A2E541E18BE6ED9" + NEWLINE
VALID_SAMPLE2 = "0409DB0A738C81747A84AC0006000A2E541E18BE6ED9" + NEWLINE

VALID_DS_RESPONSE = 'SBE 16plus V 2.2  SERIAL NO. 6841    29 Oct 2012 20:20:55' + NEWLINE + \
               'vbatt = 12.9, vlith =  8.5, ioper =  61.2 ma, ipump = 255.5 ma,' + NEWLINE + \
               'status = not logging' + NEWLINE + \
               'samples = 3684, free = 4382858' + NEWLINE + \
               'sample interval = 10 seconds, number of measurements per sample = 4' + NEWLINE + \
               'pump = run pump during sample, delay before sampling = 0.0 seconds' + NEWLINE + \
               'transmit real-time = yes' + NEWLINE + \
               'battery cutoff =  7.5 volts' + NEWLINE + \
               'pressure sensor = strain gauge, range = 160.0' + NEWLINE + \
               'SBE 38 = no, SBE 50 = no, WETLABS = no, OPTODE = no, Gas Tension Device = no' + NEWLINE + \
               'Ext Volt 0 = yes, Ext Volt 1 = yes' + NEWLINE + \
               'Ext Volt 2 = no, Ext Volt 3 = no' + NEWLINE + \
               'Ext Volt 4 = no, Ext Volt 5 = no' + NEWLINE + \
               'echo characters = yes' + NEWLINE + \
               'output format = raw HEX' + NEWLINE + \
               'output salinity = no, output sound velocity = no' + NEWLINE + \
               'serial sync mode disabled' + NEWLINE

VALID_DCAL_RESPONSE = 'SBE 16plus V 2.5  SERIAL NO. 7231    21 Feb 2013 03:50:39' + NEWLINE + \
    'temperature:  07-Nov-12' + NEWLINE + \
    '   TA0 = 1.254755e-03' + NEWLINE + \
    '   TA1 = 2.758871e-04' + NEWLINE + \
    '   TA2 = -1.368268e-06' + NEWLINE + \
    '   TA3 = 1.910795e-07' + NEWLINE + \
    '   TOFFSET = 0.000000e+00' + NEWLINE + \
    'conductivity:  07-Nov-12' + NEWLINE + \
    '   G = -9.761799e-01' + NEWLINE + \
    '   H = 1.369994e-01' + NEWLINE + \
    '   I = -3.523860e-04' + NEWLINE + \
    '   J = 4.404252e-05' + NEWLINE + \
    '   CPCOR = -9.570000e-08' + NEWLINE + \
    '   CTCOR = 3.250000e-06' + NEWLINE + \
    '   CSLOPE = 1.000000e+00' + NEWLINE + \
    'pressure S/N = 125270, range = 1000 psia:  02-nov-12' + NEWLINE + \
    '   PC1 = -4.642673e+03' + NEWLINE + \
    '   PC2 = -4.611640e-03' + NEWLINE + \
    '   PC3 = 8.921190e-04' + NEWLINE + \
    '   PD1 = 7.024800e-02' + NEWLINE + \
    '   PD2 = 0.000000e+00' + NEWLINE + \
    '   PT1 = 3.022595e+01' + NEWLINE + \
    '   PT2 = -1.549720e-04' + NEWLINE + \
    '   PT3 = 2.677750e-06' + NEWLINE + \
    '   PT4 = 1.705490e-09' + NEWLINE + \
    '   PSLOPE = 1.000000e+00' + NEWLINE + \
    '   POFFSET = 0.000000e+00' + NEWLINE + \
    'volt 0: offset = -4.650526e-02, slope = 1.246381e+00' + NEWLINE + \
    'volt 1: offset = -4.618105e-02, slope = 1.247197e+00' + NEWLINE + \
    'volt 2: offset = -4.659790e-02, slope = 1.247601e+00' + NEWLINE + \
    'volt 3: offset = -4.502421e-02, slope = 1.246911e+00' + NEWLINE + \
    'volt 4: offset = -4.589158e-02, slope = 1.246346e+00' + NEWLINE + \
    'volt 5: offset = -4.609895e-02, slope = 1.247868e+00' + NEWLINE + \
    '   EXTFREQSF = 9.999949e-01' + NEWLINE

class SeaBird16plusMixin(DriverTestMixin):
    '''
    Mixin class used for storing data particle constance and common data assertion methods.
    '''
    # Create some short names for the parameter test config
    TYPE      = ParameterTestConfigKey.TYPE
    READONLY  = ParameterTestConfigKey.READONLY
    STARTUP   = ParameterTestConfigKey.STARTUP
    DA        = ParameterTestConfigKey.DIRECT_ACCESS
    VALUE     = ParameterTestConfigKey.VALUE
    REQUIRED  = ParameterTestConfigKey.REQUIRED
    DEFAULT   = ParameterTestConfigKey.DEFAULT

    ###
    #  Parameter and Type Definitions
    ###
    _driver_parameters = {
        # Parameters defined in the IOS
        Parameter.DATE_TIME : {TYPE: str, READONLY: True, DA: False, STARTUP: False},
        Parameter.ECHO : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.OUTPUT_EXEC_TAG : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.TXREALTIME : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.PUMP_MODE : {TYPE: int, READONLY: True, DA: True, STARTUP: True, DEFAULT: 2, VALUE: 2},
        Parameter.NCYCLES : {TYPE: int, READONLY: False, DA: False, STARTUP: True, DEFAULT: 4, VALUE: 4},
        Parameter.INTERVAL : {TYPE: int, READONLY: False, DA: False, STARTUP: True, VALUE: 10},
        Parameter.BIOWIPER : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.PTYPE : {TYPE: int, READONLY: True, DA: True, STARTUP: True, DEFAULT: 1, VALUE: 1},
        Parameter.VOLT0 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.VOLT1 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.VOLT2 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.VOLT3 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.VOLT4 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.VOLT5 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.DELAY_BEFORE_SAMPLE : {TYPE: float, READONLY: True, DA: True, STARTUP: True, DEFAULT: 0.0, VALUE: 0.0},
        Parameter.DELAY_AFTER_SAMPLE : {TYPE: float, READONLY: True, DA: True, STARTUP: True, DEFAULT: 0.0, VALUE: 0.0, REQUIRED: False},
        Parameter.SBE63 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False, REQUIRED: False},
        Parameter.SBE38 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.SBE50 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.WETLABS : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.GTD : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.OPTODE : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.SYNCMODE : {TYPE: bool, READONLY: False, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.SYNCWAIT : {TYPE: bool, READONLY: False, DA: True, STARTUP: True, DEFAULT: 0, VALUE: 0, REQUIRED: False},
        Parameter.OUTPUT_FORMAT : {TYPE: int, READONLY: True, DA: True, STARTUP: True, DEFAULT: 0, VALUE: 0},
        Parameter.LOGGING : {TYPE: bool, READONLY: True, DA: False, STARTUP: False},
    }

    _sample_parameters = {
        SBE16DataParticleKey.TEMP: {TYPE: int, VALUE: 264667, REQUIRED: True },
        SBE16DataParticleKey.CONDUCTIVITY: {TYPE: int, VALUE: 684940, REQUIRED: True },
        SBE16DataParticleKey.PRESSURE: {TYPE: int, VALUE: 8483962, REQUIRED: True },
        SBE16DataParticleKey.PRESSURE_TEMP: {TYPE: int, VALUE: 33964, REQUIRED: True },
        SBE16DataParticleKey.TIME: {TYPE: int, VALUE: 415133401, REQUIRED: True },
    }

    _status_parameters = {
        SBE16StatusParticleKey.FIRMWARE_VERSION: {TYPE: unicode, VALUE: '2.2', REQUIRED: True },
        SBE16StatusParticleKey.SERIAL_NUMBER: {TYPE: int, VALUE: 6841, REQUIRED: True },
        SBE16StatusParticleKey.DATE_TIME: {TYPE: unicode, VALUE: '29 Oct 2012 20:20:55', REQUIRED: True },
        SBE16StatusParticleKey.VBATT: {TYPE: float, VALUE: 12.9, REQUIRED: True },
        SBE16StatusParticleKey.VLITH: {TYPE: float, VALUE: 8.5, REQUIRED: True },
        SBE16StatusParticleKey.IOPER: {TYPE: float, VALUE: 61.2, REQUIRED: True },
        SBE16StatusParticleKey.IPUMP: {TYPE: float, VALUE: 255.5, REQUIRED: True },
        SBE16StatusParticleKey.STATUS: {TYPE: unicode, VALUE: 'not logging', REQUIRED: True },
        SBE16StatusParticleKey.SAMPLES: {TYPE: int, VALUE: 3684, REQUIRED: True },
        SBE16StatusParticleKey.FREE: {TYPE: int, VALUE: 4382858, REQUIRED: True },
        SBE16StatusParticleKey.SAMPLE_INTERVAL: {TYPE: unicode, VALUE: '10 seconds', REQUIRED: True },
        SBE16StatusParticleKey.MEASUREMENTS_PER_SAMPLE: {TYPE: int, VALUE: 4, REQUIRED: True },
        SBE16StatusParticleKey.PUMP_MODE: {TYPE: unicode, VALUE: 'run pump during sample', REQUIRED: True },
        SBE16StatusParticleKey.DELAY_BEFORE_SAMPLING: {TYPE: float, VALUE: 0.0, REQUIRED: True },
        SBE16StatusParticleKey.DELAY_AFTER_SAMPLING: {TYPE: float, VALUE: 0.0, REQUIRED: False },
        SBE16StatusParticleKey.TX_REAL_TIME: {TYPE: bool, VALUE: True, REQUIRED: True },
        SBE16StatusParticleKey.BATTERY_CUTOFF: {TYPE: float, VALUE: 7.5, REQUIRED: True },
        SBE16StatusParticleKey.PRESSURE_SENSOR: {TYPE: unicode, VALUE: 'strain gauge', REQUIRED: True },
        SBE16StatusParticleKey.RANGE: {TYPE: float, VALUE: 160, REQUIRED: True },
        SBE16StatusParticleKey.SBE38: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.SBE50: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.WETLABS: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.OPTODE: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.GAS_TENSION_DEVICE: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.EXT_VOLT_0: {TYPE: bool, VALUE: True, REQUIRED: True },
        SBE16StatusParticleKey.EXT_VOLT_1: {TYPE: bool, VALUE: True, REQUIRED: True },
        SBE16StatusParticleKey.EXT_VOLT_2: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.EXT_VOLT_3: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.EXT_VOLT_4: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.EXT_VOLT_5: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.ECHO_CHARACTERS: {TYPE: bool, VALUE: True, REQUIRED: True },
        SBE16StatusParticleKey.OUTPUT_FORMAT: {TYPE: unicode, VALUE: 'raw HEX', REQUIRED: True },
        SBE16StatusParticleKey.OUTPUT_SALINITY: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.OUTPUT_SOUND_VELOCITY: {TYPE: bool, VALUE: False, REQUIRED: True },
        SBE16StatusParticleKey.SERIAL_SYNC_MODE: {TYPE: bool, VALUE: False, REQUIRED: True },
    }

    _calibration_parameters = {
        SBE16CalibrationParticleKey.FIRMWARE_VERSION: {TYPE: unicode, VALUE: "2.5", REQUIRED: True },
        SBE16CalibrationParticleKey.SERIAL_NUMBER: {TYPE: int, VALUE: 7231, REQUIRED: True },
        SBE16CalibrationParticleKey.DATE_TIME: {TYPE: unicode, VALUE: "21 Feb 2013 03:50:39", REQUIRED: True },
        SBE16CalibrationParticleKey.TEMP_CAL_DATE: {TYPE: unicode, VALUE: "07-Nov-12", REQUIRED: True },
        SBE16CalibrationParticleKey.TA0: {TYPE: float, VALUE: 1.254755e-03, REQUIRED: True },
        SBE16CalibrationParticleKey.TA1: {TYPE: float, VALUE: 2.758871e-04, REQUIRED: True },
        SBE16CalibrationParticleKey.TA2: {TYPE: float, VALUE: -1.368268e-06, REQUIRED: True },
        SBE16CalibrationParticleKey.TA3: {TYPE: float, VALUE: 1.910795e-07, REQUIRED: True },
        SBE16CalibrationParticleKey.TOFFSET: {TYPE: float, VALUE: 0.0, REQUIRED: True },
        SBE16CalibrationParticleKey.COND_CAL_DATE: {TYPE: unicode, VALUE: '07-Nov-12', REQUIRED: True },
        SBE16CalibrationParticleKey.CONDG: {TYPE: float, VALUE: -9.761799e-01, REQUIRED: True },
        SBE16CalibrationParticleKey.CONDH: {TYPE: float, VALUE: 1.369994e-01, REQUIRED: True },
        SBE16CalibrationParticleKey.CONDI: {TYPE: float, VALUE: -3.523860e-04, REQUIRED: True },
        SBE16CalibrationParticleKey.CONDJ: {TYPE: float, VALUE: 4.404252e-05, REQUIRED: True },
        SBE16CalibrationParticleKey.CPCOR: {TYPE: float, VALUE: -9.570000e-08, REQUIRED: True },
        SBE16CalibrationParticleKey.CTCOR: {TYPE: float, VALUE: 3.250000e-06, REQUIRED: True },
        SBE16CalibrationParticleKey.CSLOPE: {TYPE: float, VALUE: 1.000000e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.PRES_SERIAL_NUMBER: {TYPE: int, VALUE: 125270, REQUIRED: True },
        SBE16CalibrationParticleKey.PRES_RANGE: {TYPE: int, VALUE: 1000, REQUIRED: True },
        SBE16CalibrationParticleKey.PRES_CAL_DATE: {TYPE: unicode, VALUE: '02-nov-12', REQUIRED: True },
        SBE16CalibrationParticleKey.PC1: {TYPE: float, VALUE: -4.642673e+03, REQUIRED: True },
        SBE16CalibrationParticleKey.PC2: {TYPE: float, VALUE: -4.611640e-03, REQUIRED: True },
        SBE16CalibrationParticleKey.PC3: {TYPE: float, VALUE: 8.921190e-04, REQUIRED: True },
        SBE16CalibrationParticleKey.PD1: {TYPE: float, VALUE: 7.024800e-02, REQUIRED: True },
        SBE16CalibrationParticleKey.PD2: {TYPE: float, VALUE: 0.000000e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.PT1: {TYPE: float, VALUE: 3.022595e+01, REQUIRED: True },
        SBE16CalibrationParticleKey.PT2: {TYPE: float, VALUE: -1.549720e-04, REQUIRED: True },
        SBE16CalibrationParticleKey.PT3: {TYPE: float, VALUE: 2.677750e-06, REQUIRED: True },
        SBE16CalibrationParticleKey.PT4: {TYPE: float, VALUE: 1.705490e-09, REQUIRED: True },
        SBE16CalibrationParticleKey.PSLOPE: {TYPE: float, VALUE: 1.000000e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.POFFSET: {TYPE: float, VALUE: 0.000000e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT0_OFFSET: {TYPE: float, VALUE: -4.650526e-02, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT0_SLOPE: {TYPE: float, VALUE: 1.246381e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT1_OFFSET: {TYPE: float, VALUE: -4.618105e-02, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT1_SLOPE: {TYPE: float, VALUE: 1.247197e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT2_OFFSET: {TYPE: float, VALUE: -4.659790e-02, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT2_SLOPE: {TYPE: float, VALUE: 1.247601e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT3_OFFSET: {TYPE: float, VALUE: -4.502421e-02, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT3_SLOPE: {TYPE: float, VALUE: 1.246911e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT4_OFFSET: {TYPE: float, VALUE: -4.589158e-02, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT4_SLOPE: {TYPE: float, VALUE: 1.246346e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT5_OFFSET: {TYPE: float, VALUE: -4.609895e-02, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_VOLT5_SLOPE: {TYPE: float, VALUE: 1.247868e+00, REQUIRED: True },
        SBE16CalibrationParticleKey.EXT_FREQ: {TYPE: float, VALUE: 9.999949e-01, REQUIRED: True },
    }

    ###
    #   Driver Parameter Methods
    ###
    def assert_driver_parameters(self, current_parameters, verify_values = False):
        """
        Verify that all driver parameters are correct and potentially verify values.
        @param current_parameters: driver parameters read from the driver instance
        @param verify_values: should we verify values against definition?
        """
        self.assert_parameters(current_parameters, self._driver_parameters, verify_values)

    def assert_particle_sample(self, data_particle, verify_values = False):
        '''
        Verify sample particle
        @param data_particle:  SBE16DataParticle data particle
        @param verify_values:  bool, should we verify parameter values
        '''
        self.assert_data_particle_keys(SBE16DataParticleKey, self._sample_parameters)
        self.assert_data_particle_header(data_particle, DataParticleType.CTD_PARSED, require_instrument_timestamp=True)
        self.assert_data_particle_parameters(data_particle, self._sample_parameters, verify_values)

    def assert_particle_status(self, data_particle, verify_values = False):
        '''
        Verify status particle
        @param data_particle:  SBE16StatusParticle data particle
        @param verify_values:  bool, should we verify parameter values
        '''
        self.assert_data_particle_keys(SBE16StatusParticleKey, self._status_parameters)
        self.assert_data_particle_header(data_particle, DataParticleType.DEVICE_STATUS)
        self.assert_data_particle_parameters(data_particle, self._status_parameters, verify_values)

    def assert_particle_calibration(self, data_particle, verify_values = False):
        '''
        Verify calibration particle
        @param data_particle:  SBE16CalibrationParticle data particle
        @param verify_values:  bool, should we verify parameter values
        '''
        self.assert_data_particle_keys(SBE16CalibrationParticleKey, self._calibration_parameters)
        self.assert_data_particle_header(data_particle, DataParticleType.DEVICE_CALIBRATION)
        self.assert_data_particle_parameters(data_particle, self._calibration_parameters, verify_values)

#################################### RULES ####################################
#                                                                             #
# Common capabilities in the base class                                       #
#                                                                             #
# Instrument specific stuff in the derived class                              #
#                                                                             #
# Generator spits out either stubs or comments describing test this here,     #
# test that there.                                                            #
#                                                                             #
# Qualification tests are driven through the instrument_agent                 #
#                                                                             #
###############################################################################

###############################################################################
#                                UNIT TESTS                                   #
#         Unit tests test the method calls and parameters using Mock.         #
###############################################################################

@attr('UNIT', group='mi')
class SBEUnitTestCase(SeaBirdUnitTest, SeaBird16plusMixin):
    """Unit Test Driver"""
    def test_driver_enums(self):
        """
        Verify that all driver enumeration has no duplicate values that might cause confusion.  Also
        do a little extra validation for the Capabilites
        """
        self.assert_enum_has_no_duplicates(Command())
        self.assert_enum_has_no_duplicates(ScheduledJob())
        self.assert_enum_has_no_duplicates(DataParticleType())
        self.assert_enum_has_no_duplicates(ProtocolState())
        self.assert_enum_has_no_duplicates(ProtocolEvent())
        self.assert_enum_has_no_duplicates(Parameter())

        # Test capabilites for duplicates, them verify that capabilities is a subset of proto events
        self.assert_enum_has_no_duplicates(Capability())
        self.assert_enum_complete(Capability(), ProtocolEvent())

    def test_chunker(self):
        """
        Test the chunker and verify the particles created.
        """
        chunker = StringChunker(SBE16Protocol.sieve_function)

        self.assert_chunker_sample(chunker, VALID_SAMPLE)
        self.assert_chunker_sample_with_noise(chunker, VALID_SAMPLE)
        self.assert_chunker_fragmented_sample(chunker, VALID_SAMPLE)
        self.assert_chunker_combined_sample(chunker, VALID_SAMPLE)

        self.assert_chunker_sample(chunker, VALID_SAMPLE2)
        self.assert_chunker_sample_with_noise(chunker, VALID_SAMPLE2)
        self.assert_chunker_fragmented_sample(chunker, VALID_SAMPLE2)
        self.assert_chunker_combined_sample(chunker, VALID_SAMPLE2)

        self.assert_chunker_sample(chunker, VALID_DS_RESPONSE)
        self.assert_chunker_sample_with_noise(chunker, VALID_DS_RESPONSE)
        self.assert_chunker_fragmented_sample(chunker, VALID_DS_RESPONSE, 64)
        self.assert_chunker_combined_sample(chunker, VALID_DS_RESPONSE)

        self.assert_chunker_sample(chunker, VALID_DCAL_RESPONSE)
        self.assert_chunker_sample_with_noise(chunker, VALID_DCAL_RESPONSE)
        self.assert_chunker_fragmented_sample(chunker, VALID_DCAL_RESPONSE, 64)
        self.assert_chunker_combined_sample(chunker, VALID_DCAL_RESPONSE)

    def test_got_data(self):
        """
        Verify sample data passed through the got data method produces the correct data particles
        """
        # Create and initialize the instrument driver with a mock port agent
        driver = SBE16InstrumentDriver(self._got_data_event_callback)
        self.assert_initialize_driver(driver)

        #self.assert_raw_particle_published(driver, True)

        # Start validating data particles
        self.assert_particle_published(driver, VALID_SAMPLE, self.assert_particle_sample, True)
        self.assert_particle_published(driver, VALID_SAMPLE2, self.assert_particle_sample, True)
        self.assert_particle_published(driver, VALID_DS_RESPONSE, self.assert_particle_status, True)
        self.assert_particle_published(driver, VALID_DCAL_RESPONSE, self.assert_particle_calibration, True)

    def test_protocol_filter_capabilities(self):
        """
        This tests driver filter_capabilities.
        Iterate through available capabilities, and verify that they can pass successfully through the filter.
        Test silly made up capabilities to verify they are blocked by filter.
        """
        my_event_callback = Mock(spec="UNKNOWN WHAT SHOULD GO HERE FOR evt_callback")
        protocol = SBE16Protocol(Prompt, NEWLINE, my_event_callback)
        driver_capabilities = Capability().list()
        test_capabilities = Capability().list()

        # Add a bogus capability that will be filtered out.
        test_capabilities.append("BOGUS_CAPABILITY")

        # Verify "BOGUS_CAPABILITY was filtered out
        self.assertEquals(driver_capabilities, protocol._filter_capabilities(test_capabilities))

    def test_driver_parameters(self):
        """
        Verify the set of parameters known by the driver
        """
        driver = SBE16InstrumentDriver(self._got_data_event_callback)
        self.assert_initialize_driver(driver, ProtocolState.COMMAND)

        expected_parameters = sorted(self._driver_parameters.keys())
        reported_parameters = sorted(driver.get_resource(Parameter.ALL))

        log.debug("Reported Parameters: %s" % reported_parameters)
        log.debug("Expected Parameters: %s" % expected_parameters)

        self.assertEqual(reported_parameters, expected_parameters)

        # Verify the parameter definitions
        self.assert_driver_parameter_definition(driver, self._driver_parameters)

    def test_capabilities(self):
        """
        Verify the FSM reports capabilities as expected.  All states defined in this dict must
        also be defined in the protocol FSM.
        """
        capabilities = {
            ProtocolState.UNKNOWN: ['DRIVER_EVENT_DISCOVER'],
            ProtocolState.TEST: ['DRIVER_EVENT_GET',
                                 'DRIVER_EVENT_RUN_TEST'],
            ProtocolState.COMMAND: ['DRIVER_EVENT_ACQUIRE_SAMPLE',
                                    'DRIVER_EVENT_ACQUIRE_STATUS',
                                    'DRIVER_EVENT_CLOCK_SYNC',
                                    'DRIVER_EVENT_GET',
                                    'DRIVER_EVENT_SET',
                                    'DRIVER_EVENT_TEST',
                                    'DRIVER_EVENT_START_AUTOSAMPLE',
                                    'DRIVER_EVENT_START_DIRECT',
                                    'PROTOCOL_EVENT_GET_CONFIGURATION',
                                    'DRIVER_EVENT_SCHEDULED_CLOCK_SYNC'],
            ProtocolState.AUTOSAMPLE: ['DRIVER_EVENT_GET',
                                       'DRIVER_EVENT_STOP_AUTOSAMPLE',
                                       'PROTOCOL_EVENT_GET_CONFIGURATION',
                                       'DRIVER_EVENT_SCHEDULED_CLOCK_SYNC',
                                       'DRIVER_EVENT_ACQUIRE_STATUS'],
            ProtocolState.DIRECT_ACCESS: ['DRIVER_EVENT_STOP_DIRECT', 'EXECUTE_DIRECT']
        }

        driver = SBE16InstrumentDriver(self._got_data_event_callback)
        self.assert_capabilities(driver, capabilities)

    def test_parse_ds(self):
        """
        Create a mock port agent
        """
        driver = SBE16InstrumentDriver(self._got_data_event_callback)
        self.assert_initialize_driver(driver, ProtocolState.COMMAND)
        source = VALID_DS_RESPONSE

        # First verify that parse ds sets all know parameters.
        driver._protocol._parse_dsdc_response(source, '<Executed/>')
        pd = driver._protocol._param_dict.get_config()
        log.debug("Param Dict Values: %s" % pd)
        log.debug("Param Sample: %s" % source)
        self.assert_driver_parameters(pd, True)

        # Now change some things and make sure they are parsed properly
        # Note:  Only checking parameters that can change.

        # Logging
        source = source.replace("= not logging", "= logging")
        log.debug("Param Sample: %s" % source)
        driver._protocol._parse_dsdc_response(source, '<Executed/>')
        pd = driver._protocol._param_dict.get_config()
        self.assertTrue(pd.get(Parameter.LOGGING))

        # Sync Mode
        source = source.replace("serial sync mode disabled", "serial sync mode enabled")
        log.debug("Param Sample: %s" % source)
        driver._protocol._parse_dsdc_response(source, '<Executed/>')
        pd = driver._protocol._param_dict.get_config()
        self.assertTrue(pd.get(Parameter.SYNCMODE))


###############################################################################
#                            INTEGRATION TESTS                                #
#     Integration test test the direct driver / instrument interaction        #
#     but making direct calls via zeromq.                                     #
#     - Common Integration tests test the driver through the instrument agent #
#     and common for all drivers (minmum requirement for ION ingestion)       #
###############################################################################

@attr('INT', group='mi')
class SBEIntTestCase(SeaBirdIntegrationTest):
    """
    Integration tests for the sbe16 driver. This class tests and shows
    use patterns for the sbe16 driver as a zmq driver process.
    """    
    def test_test(self):
        """
        Test the hardware testing mode.
        """
        self.assert_initialize_driver()

        timeout = time.time() + 60
        reply = self.driver_client.cmd_dvr('execute_resource', ProtocolEvent.TEST)

        self.assert_current_state(ProtocolState.TEST)

        # Test the driver is in test state.
        state = self.driver_client.cmd_dvr('get_resource_state')

        while state != ProtocolState.COMMAND:
            gevent.sleep(5)
            elapsed = time.time() - start_time
            log.info('Device testing %f seconds elapsed.' % elapsed)
            state = self.driver_client.cmd_dvr('get_resource_state')
            self.assertLess(time.time(), timeout, msg="Timeout waiting for instrument to come out of test")

        # Verify we received the test result and it passed.
        test_results = [evt for evt in self.events if evt['type']==DriverAsyncEvent.RESULT]
        self.assertTrue(len(test_results) == 1)
        self.assertEqual(test_results[0]['value']['success'], 'Passed')

    def test_parameters(self):
        """
        Test driver parameters and verify their type.  Startup parameters also verify the parameter
        value.  This test confirms that parameters are being read/converted properly and that
        the startup has been applied.
        """
        self.assert_initialize_driver()
        reply = self.driver_client.cmd_dvr('get_resource', Parameter.ALL)
        self.assert_driver_parameters(reply, True)

    def test_set(self):
        """
        Test all set commands. Verify all exception cases.
        """
        self.assert_initialize_driver()

        #   Instrument Parameteres

        # Sample Period.  integer 1 - 240
#        self.assert_set(Parameter.SAMPLE_PERIOD, 1)
#        self.assert_set(Parameter.SAMPLE_PERIOD, 240)
#        self.assert_set_exception(Parameter.SAMPLE_PERIOD, 241)
#        self.assert_set_exception(Parameter.SAMPLE_PERIOD, 0)
#        self.assert_set_exception(Parameter.SAMPLE_PERIOD, -1)
#        self.assert_set_exception(Parameter.SAMPLE_PERIOD, 0.2)
#        self.assert_set_exception(Parameter.SAMPLE_PERIOD, "1")

        #   Read only parameters
#        self.assert_set_readonly(Parameter.BATTERY_TYPE, 1)
#        self.assert_set_readonly(Parameter.ENABLE_ALERTS, True)

    def test_commands(self):
        """
        Run instrument commands from both command and streaming mode.
        """
        self.assert_initialize_driver()

        ####
        # First test in command mode
        ####
#        self.assert_driver_command(ProtocolEvent.START_AUTOSAMPLE, state=ProtocolState.AUTOSAMPLE, delay=1)
#        self.assert_driver_command(ProtocolEvent.STOP_AUTOSAMPLE, state=ProtocolState.COMMAND, delay=1)
#        self.assert_driver_command(ProtocolEvent.ACQUIRE_STATUS, regex=r'StatusData DeviceType')
#        self.assert_driver_command(ProtocolEvent.CLOCK_SYNC)
#        self.assert_driver_command(ProtocolEvent.SCHEDULED_CLOCK_SYNC)
#        self.assert_driver_command(ProtocolEvent.GET_CONFIGURATION_DATA, regex=r'ConfigurationData DeviceType')
#        self.assert_driver_command(ProtocolEvent.GET_HARDWARE_DATA, regex=r'HardwareData DeviceType')
#        self.assert_driver_command(ProtocolEvent.GET_STATUS_DATA, regex=r'StatusData DeviceType')
#        self.assert_driver_command(ProtocolEvent.GET_EVENT_COUNTER, regex=r'EventList DeviceType')
#        self.assert_driver_command(ProtocolEvent.SAMPLE_REFERENCE_OSCILLATOR, regex=r'Ref osc warmup')

        ####
        # Test in streaming mode
        ####
        # Put us in streaming
#        self.assert_driver_command(ProtocolEvent.START_AUTOSAMPLE, state=ProtocolState.AUTOSAMPLE, delay=1)

#        self.assert_driver_command(ProtocolEvent.ACQUIRE_STATUS, regex=r'StatusData DeviceType')
#        self.assert_driver_command(ProtocolEvent.SCHEDULED_CLOCK_SYNC)
#        self.assert_driver_command(ProtocolEvent.GET_CONFIGURATION_DATA, regex=r'ConfigurationData DeviceType')
#        self.assert_driver_command(ProtocolEvent.GET_HARDWARE_DATA, regex=r'HardwareData DeviceType')
#        self.assert_driver_command(ProtocolEvent.GET_STATUS_DATA, regex=r'StatusData DeviceType')
#        self.assert_driver_command(ProtocolEvent.GET_EVENT_COUNTER, regex=r'EventList DeviceType')

#        self.assert_driver_command(ProtocolEvent.STOP_AUTOSAMPLE, state=ProtocolState.COMMAND, delay=1)

        ####
        # Test a bad command
        ####
#        self.assert_driver_command_exception('ima_bad_command', exception_class=InstrumentCommandException)

    def test_autosample(self):
        """
        Verify that we can enter streaming and that all particles are produced
        properly.

        Because we have to test for three different data particles we can't use
        the common assert_sample_autosample method
        """
        self.assert_initialize_driver()
#        self.assert_set(Parameter.SAMPLE_PERIOD, 1)

#        self.assert_driver_command(ProtocolEvent.START_AUTOSAMPLE, state=ProtocolState.AUTOSAMPLE, delay=1)
#        self.assert_async_particle_generation(DataParticleType.PREST_REAL_TIME, self.assert_particle_real_time, timeout=120)

#        self.assert_particle_generation(ProtocolEvent.GET_CONFIGURATION_DATA, DataParticleType.PREST_CONFIGURATION_DATA, self.assert_particle_configuration_data)
#        self.assert_particle_generation(ProtocolEvent.GET_STATUS_DATA, DataParticleType.PREST_DEVICE_STATUS, self.assert_particle_device_status)
#        self.assert_particle_generation(ProtocolEvent.GET_EVENT_COUNTER, DataParticleType.PREST_EVENT_COUNTER, self.assert_particle_event_counter)
#        self.assert_particle_generation(ProtocolEvent.GET_HARDWARE_DATA, DataParticleType.PREST_HARDWARE_DATA, self.assert_particle_hardware_data)

#        self.assert_driver_command(ProtocolEvent.STOP_AUTOSAMPLE, state=ProtocolState.COMMAND, delay=1)

    def test_polled(self):
        """
        Test that we can generate particles with commands
        """
        self.assert_initialize_driver()

#        self.assert_particle_generation(ProtocolEvent.GET_CONFIGURATION_DATA, DataParticleType.PREST_CONFIGURATION_DATA, self.assert_particle_configuration_data)
#        self.assert_particle_generation(ProtocolEvent.GET_STATUS_DATA, DataParticleType.PREST_DEVICE_STATUS, self.assert_particle_device_status)
#        self.assert_particle_generation(ProtocolEvent.GET_EVENT_COUNTER, DataParticleType.PREST_EVENT_COUNTER, self.assert_particle_event_counter)
#        self.assert_particle_generation(ProtocolEvent.GET_HARDWARE_DATA, DataParticleType.PREST_HARDWARE_DATA, self.assert_particle_hardware_data)

#        self.assert_particle_generation(ProtocolEvent.SAMPLE_REFERENCE_OSCILLATOR, DataParticleType.PREST_REFERENCE_OSCILLATOR, self.assert_particle_reference_oscillator)

    def test_apply_startup_params(self):
        """
        This test verifies that we can set the startup params
        from autosample mode.  It only verifies one parameter
        change because all parameters are tested above.
        """
        # Apply autosample happens for free when the driver fires up
        self.assert_initialize_driver()
        ##
        ## Build common apply startup tests using list of tuples
        ##

        # Change something
#        self.assert_set(Parameter.SAMPLE_PERIOD, 10)

        # Now try to apply params in Streaming
#        self.assert_driver_command(ProtocolEvent.START_AUTOSAMPLE, state=ProtocolState.AUTOSAMPLE)
#        self.driver_client.cmd_dvr('apply_startup_params')

        # All done.  Verify the startup parameter has been reset
#        self.assert_driver_command(ProtocolEvent.STOP_AUTOSAMPLE, state=ProtocolState.COMMAND)
#        self.assert_get(Parameter.SAMPLE_PERIOD, 15)

    def test_startup_params_first_pass(self):
        """
        Verify that startup parameters are applied correctly. Generally this
        happens in the driver discovery method.  We have two identical versions
        of this test so it is run twice.  First time to check and CHANGE, then
        the second time to check again.

        since nose orders the tests by ascii value this should run first.
        """
        self.assert_initialize_driver()

#        self.assert_get(Parameter.SAMPLE_PERIOD, 15)

        # Now change them so they are caught and see if they are caught
        # on the second pass.
#        self.assert_set(Parameter.SAMPLE_PERIOD, 5)

    def test_startup_params_second_pass(self):
        """
        Verify that startup parameters are applied correctly. Generally this
        happens in the driver discovery method.  We have two identical versions
        of this test so it is run twice.  First time to check and CHANGE, then
        the second time to check again.

        since nose orders the tests by ascii value this should run second.
        """
        self.assert_initialize_driver()

#        self.assert_get(Parameter.SAMPLE_PERIOD, 15)

        # Now change them so they are caught and see if they are caught
        # on the second pass.
#        self.assert_set(Parameter.SAMPLE_PERIOD, 5)


###############################################################################
#                            QUALIFICATION TESTS                              #
# Device specific qualification tests are for                                 #
# testing device specific capabilities                                        #
###############################################################################

@attr('QUAL', group='mi')
class SBEQualTestCase(SeaBirdQualificationTest):
    """Qualification Test Container"""

    # Qualification tests live in the base class.  This class is extended
    # here so that when running this test from 'nosetests' all tests
    # (UNIT, INT, and QUAL) are run.
    @unittest.skip("Not working; not sure why...")
    def test_execute_test(self):
        """
        Test the hardware testing mode.
        """
        self.data_subscribers.start_data_subscribers()
        self.addCleanup(self.data_subscribers.stop_data_subscribers)

        state = self.instrument_agent_client.get_agent_state()
        self.assertEqual(state, ResourceAgentState.UNINITIALIZED)

        cmd = AgentCommand(command=ResourceAgentEvent.INITIALIZE)
        retval = self.instrument_agent_client.execute_agent(cmd)
        state = self.instrument_agent_client.get_agent_state()
        self.assertEqual(state, ResourceAgentState.INACTIVE)

        cmd = AgentCommand(command=ResourceAgentEvent.GO_ACTIVE)
        retval = self.instrument_agent_client.execute_agent(cmd)
        state = self.instrument_agent_client.get_agent_state()
        self.assertEqual(state, ResourceAgentState.IDLE)

        cmd = AgentCommand(command=ResourceAgentEvent.RUN)
        retval = self.instrument_agent_client.execute_agent(cmd)
        state = self.instrument_agent_client.get_agent_state()
        self.assertEqual(state, ResourceAgentState.COMMAND)

        #### From herehere down convert to agent-version
        start_time = time.time()
        cmd = AgentCommand(command=ProtocolEvent.TEST)
        retval = self.instrument_agent_client.execute_resource(cmd)

        # Test the driver is in test state.
        state = self.instrument_agent_client.get_agent_state()
        self.assertEqual(state, ResourceAgentState.TEST)
        
        while state != ResourceAgentState.COMMAND:
            gevent.sleep(5)
            elapsed = time.time() - start_time
            state = self.instrument_agent_client.get_agent_state()
            log.info('Device testing %f seconds elapsed. ResourceAgentState: %s' % (elapsed, state))

        """
        # Verify we received the test result and it passed.
        #test_results = [evt for evt in self.events if evt['type']==DriverAsyncEvent.TEST_RESULT]
        test_results = [evt for evt in self.events if evt['type']==DriverAsyncEvent.RESULT]
        self.assertTrue(len(test_results) == 1)
        self.assertEqual(test_results[0]['value']['success'], 'Passed')

        cmd = AgentCommand(command=ResourceAgentEvent.RESET)
        retval = self.instrument_agent_client.execute_agent(cmd)
        state = self.instrument_agent_client.get_agent_state()
        self.assertEqual(state, ResourceAgentState.UNINITIALIZED)

        """

    def test_autosample(self):
        """
        Verify autosample works and data particles are created
        """
        self.assert_enter_command_mode()
#        self.assert_set_parameter(Parameter.SAMPLE_PERIOD, 1)

#        self.assert_sample_autosample(self.assert_particle_real_time, DataParticleType.PREST_REAL_TIME)

    def test_poll(self):
        '''
        Verify that we can poll for a sample.  Take sample for this instrument
        Also poll for other engineering data streams.
        '''
        self.assert_enter_command_mode()

#        self.assert_particle_polled(ProtocolEvent.GET_HARDWARE_DATA, self.assert_particle_hardware_data, DataParticleType.PREST_HARDWARE_DATA, sample_count=1)
#        self.assert_particle_polled(ProtocolEvent.GET_STATUS_DATA, self.assert_particle_device_status, DataParticleType.PREST_DEVICE_STATUS, sample_count=1)
#        self.assert_particle_polled(ProtocolEvent.GET_EVENT_COUNTER, self.assert_particle_event_counter, DataParticleType.PREST_EVENT_COUNTER, sample_count=1)
#        self.assert_particle_polled(ProtocolEvent.GET_CONFIGURATION_DATA, self.assert_particle_configuration_data, DataParticleType.PREST_CONFIGURATION_DATA, sample_count=1)
#        self.assert_particle_polled(ProtocolEvent.SAMPLE_REFERENCE_OSCILLATOR, self.assert_particle_reference_oscillator, DataParticleType.PREST_REFERENCE_OSCILLATOR, sample_count=1, timeout=200)

    def test_direct_access_telnet_mode(self):
        """
        @brief This test manually tests that the Instrument Driver properly supports direct access to the physical instrument. (telnet mode)
        """
        self.assert_enter_command_mode()
#        self.assert_set_parameter(Parameter.SAMPLE_PERIOD, 5)

#        # go into direct access, and muck up a setting.
#        self.assert_direct_access_start_telnet(timeout=600)
#        self.assertTrue(self.tcp_client)
#        self.tcp_client.send_data("%ssetSamplePeriod=97%s" % (NEWLINE, NEWLINE))
#        self.tcp_client.expect("S>")

#        self.assert_direct_access_stop_telnet()

        # verify the setting got restored.
#        self.assert_enter_command_mode()
#        self.assert_get_parameter(Parameter.SAMPLE_PERIOD, 5)

    def test_execute_clock_sync(self):
        """
        Verify we can syncronize the instrument internal clock
        """
#        self.assert_enter_command_mode()

        # wait for a bit so the event can be triggered
#        time.sleep(1)

        # Set the clock to something in the past
#        self.assert_set_parameter(Parameter.TIME, "2001-01-01T01:01:01", verify=False)

#        self.assert_execute_resource(ProtocolEvent.CLOCK_SYNC)
#        self.assert_execute_resource(ProtocolEvent.ACQUIRE_STATUS)

        # Now verify that at least the date matches
#        params = [Parameter.TIME]
#        check_new_params = self.instrument_agent_client.get_resource(params)
#        lt = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.mktime(time.localtime())))
#        log.debug("TIME: %s && %s" % (lt, check_new_params[Parameter.TIME]))
#        self.assertTrue(lt[:12].upper() in check_new_params[Parameter.TIME].upper())

    def test_startup_params_first_pass(self):
        """
        Verify that startup parameters are applied correctly. Generally this
        happens in the driver discovery method.  We have two identical versions
        of this test so it is run twice.  First time to check and CHANGE, then
        the second time to check again.

        since nose orders the tests by ascii value this should run second.
        """
        self.assert_enter_command_mode()

#        self.assert_get_parameter(Parameter.SAMPLE_PERIOD, 15)

        # Change these values anyway just in case it ran first.
#        self.assert_set_parameter(Parameter.SAMPLE_PERIOD, 5)

    def test_startup_params_second_pass(self):
        """
        Verify that startup parameters are applied correctly. Generally this
        happens in the driver discovery method.  We have two identical versions
        of this test so it is run twice.  First time to check and CHANGE, then
        the second time to check again.

        since nose orders the tests by ascii value this should run second.
        """
        self.assert_enter_command_mode()

#        self.assert_get_parameter(Parameter.SAMPLE_PERIOD, 15)

        # Change these values anyway just in case it ran first.
#        self.assert_set_parameter(Parameter.SAMPLE_PERIOD, 5)

    def test_get_capabilities(self):
        """
        @brief Verify that the correct capabilities are returned from get_capabilities
        at various driver/agent states.
        """
        self.assert_enter_command_mode()

        ##################
        #  Command Mode
        ##################
#        capabilities = {
#            AgentCapabilityType.AGENT_COMMAND: self._common_agent_commands(ResourceAgentState.COMMAND),
#            AgentCapabilityType.AGENT_PARAMETER: self._common_agent_parameters(),
#            AgentCapabilityType.RESOURCE_COMMAND: [
#                ProtocolEvent.START_AUTOSAMPLE,
#                ProtocolEvent.ACQUIRE_STATUS,
#                ProtocolEvent.CLOCK_SYNC,
#                ProtocolEvent.GET_CONFIGURATION_DATA,
#                ProtocolEvent.GET_HARDWARE_DATA,
#                ProtocolEvent.GET_EVENT_COUNTER,
#                ProtocolEvent.GET_STATUS_DATA,
#                ProtocolEvent.SAMPLE_REFERENCE_OSCILLATOR,
#                ProtocolEvent.TEST_EEPROM,
#                ],
#            AgentCapabilityType.RESOURCE_INTERFACE: None,
#            AgentCapabilityType.RESOURCE_PARAMETER: self._driver_parameters.keys()
#        }

#        self.assert_capabilities(capabilities)

        ##################
        #  Streaming Mode
        ##################

#        capabilities[AgentCapabilityType.AGENT_COMMAND] = self._common_agent_commands(ResourceAgentState.STREAMING)
#        capabilities[AgentCapabilityType.RESOURCE_COMMAND] =  [
#            ProtocolEvent.STOP_AUTOSAMPLE,
#            ProtocolEvent.ACQUIRE_STATUS,
#            ProtocolEvent.GET_CONFIGURATION_DATA,
#            ProtocolEvent.GET_HARDWARE_DATA,
#            ProtocolEvent.GET_EVENT_COUNTER,
#            ProtocolEvent.GET_STATUS_DATA,
#            ]

#        self.assert_start_autosample()
#        self.assert_capabilities(capabilities)
##        self.assert_stop_autosample()

        ##################
        #  DA Mode
        ##################

#        capabilities[AgentCapabilityType.AGENT_COMMAND] = self._common_agent_commands(ResourceAgentState.DIRECT_ACCESS)
#        capabilities[AgentCapabilityType.RESOURCE_COMMAND] = self._common_da_resource_commands()

#        self.assert_direct_access_start_telnet()
#        self.assert_capabilities(capabilities)
#        self.assert_direct_access_stop_telnet()

        #######################
        #  Uninitialized Mode
        #######################

#        capabilities[AgentCapabilityType.AGENT_COMMAND] = self._common_agent_commands(ResourceAgentState.UNINITIALIZED)
#        capabilities[AgentCapabilityType.RESOURCE_COMMAND] = []
#        capabilities[AgentCapabilityType.RESOURCE_INTERFACE] = []
#        capabilities[AgentCapabilityType.RESOURCE_PARAMETER] = []

#        self.assert_reset()
#        self.assert_capabilities(capabilities)

###############################################################################
#                             PUBLICATION TESTS                               #
# Device specific pulication tests are for                                    #
# testing device specific capabilities                                        #
###############################################################################
@attr('PUB', group='mi')
class SBEPubTestCase(SeaBirdPublicationTest):
    def test_granule_generation(self):
        self.assert_initialize_driver()

        # Currently these tests only verify that the data granule is generated, but the values
        # are not tested.  We will eventually need to replace log.debug with a better callback
        # function that actually tests the granule.
        self.assert_sample_async("raw data", log.debug, DataParticleType.RAW, timeout=10)

#        self.assert_sample_async(SAMPLE_SAMPLE, log.debug, DataParticleType.PREST_REAL_TIME, timeout=10)
#        self.assert_sample_async(SAMPLE_GETCD, log.debug, DataParticleType.PREST_CONFIGURATION_DATA, timeout=10)
#        self.assert_sample_async(SAMPLE_GETEC, log.debug, DataParticleType.PREST_EVENT_COUNTER, timeout=10)
#        self.assert_sample_async(SAMPLE_GETHD, log.debug, DataParticleType.PREST_HARDWARE_DATA, timeout=10)
#        self.assert_sample_async(SAMPLE_GETSD, log.debug, DataParticleType.PREST_DEVICE_STATUS, timeout=10)
#        self.assert_sample_async(SAMPLE_REF_OSC, log.debug, DataParticleType.PREST_REFERENCE_OSCILLATOR, timeout=10)
