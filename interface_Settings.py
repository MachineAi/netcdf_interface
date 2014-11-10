#! /usr/bin/python
# -*- coding: latin1 -*-

"""
Modul with default settings and constants.

This module contains all global constants that are used within the interface.
These global constants should not be changed. Furthermore in this module is a class
containing default values that are read from the related XML file. These values are
default values and can be changed by the user. Another class in this module defines
the logger that is used within this program.
This module can also be used by other modules that want to use these values.
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-04-15"
__version__ = "v0.1.2"


#Changelog
#-------------------------------------------------------------------------------
#2001-04-15: v0.1.3 little changes for bug with type 'Byte'
#2010-01-11: v0.1.2 new class and related XML file for default settings
#2010-11-23: v0.1.1 comments and docstrings added
#2010-10-18: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
from ctypes import * #For reading udunits library via CDLL
import xml.dom.minidom as minidom
import logging

#related libraries
#local applications / library specific import

#===============================================================================


#Global constants that should not be changed
#_______________________________________________________________________________


#Misceallenous constants
#-------------------------------------------------------------------------------
INTERFACE_LOGGER_ROOT = 'interface' #Logger root name for interface
FILENAME_DEFAULT_SETTINGS_XML = 'interface_Settings.xml' #Logger file name


#Constants declaring filename suffixes
#-------------------------------------------------------------------------------
FILENAME_SUFFIX_NCML = '__ncml.xml'
FILENAME_SUFFIX_NUMPYXML = '__coords.xml'
FILENAME_SUFFIX_NUMPYDATA = '__data.npy'

DECLARATION_NETCDF_STATION = '_time_series'

FILENAME_SUFFIX_NETCDF = '.nc'


#Constants and units related to NetCDF attributes
#-------------------------------------------------------------------------------
NETCDF_FORMAT = 'NETCDF3_CLASSIC'

#Constants declaring legal values for NetCDF coordinate variable units attribute
#Units since Unix epoch (1/1/1970)
MODEL_REFERENCE_TIME_UNITS = ['hours since 1970-01-01 00:00:0.0', 'msec since 1970-01-01 00:00:0.0']
HEIGHT_UNITS = ['m','1'] #'Level' is not conform to udunits!
LATITUDE_UNITS = ['degrees_north']
LONGITUDE_UNITS = ['degrees_east']


#Constants declaring legal values for coordinate variable names / dimension names in a NetCDF file
#-------------------------------------------------------------------------------
TIME = ['time']
HEIGHT = ['height', 'elev', 'depth']
LATITUDE = ['lat', 'latitude']
LONGITUDE = ['lon', 'longitude']
ID = ['_id']

COORD_KEYWORDS = TIME + HEIGHT + LATITUDE + LONGITUDE + ID #Coordinate variable keywords, here not data variable keywords


#Constants declaring legal values for type declaration
#-------------------------------------------------------------------------------
BOOL = ['bool', 'Bool']
BYTE = ['byte', 'int8', 'i1']#, 'Byte'] #NetCDF3, NetCDF4 #!!!Problems with string 'Byte' might occure, deactivate if necessary
#BYTE = ['byte', 'int8', 'i1', 'Byte'] #NetCDF3, NetCDF4 #!!!Problems with string 'Byte' might occure, deactivate if necessary
U_BYTE = ['ubyte', 'UByte', 'uint8', 'u1'] #NetCDF4
SHORT = ['short', 'int16', 'Int16', 'i2'] #NetCDF3, NetCDF4
U_SHORT = ['ushort', 'uint16', 'UInt16', 'u2'] #NetCDF4
INTEGER = ['int', 'int32', 'Int32', 'integer', 'i4'] #NetCDF3, NetCDF4
U_INTEGER = ['uint', 'uint32', 'UInt32', 'unsigned_integer', 'u4'] #NetCDF4
LONG = ['long', 'int64', 'Int64', 'i8'] #NetCDF4
U_LONG = ['ulong', 'uint64', 'UInt64', 'u8'] #NetCDF4
FLOAT = ['float', 'float32', 'Float32', 'f4'] #NetCDF3, NetCDF4
DOUBLE = ['float64', 'double', 'Float64', 'f8'] #NetCDF3, NetCDF4
STRING = ['char', 'string', 'S1'] #NetCDF3, NetCDF4

ALL_INTS = BYTE + U_BYTE + SHORT + U_SHORT + INTEGER + U_INTEGER + LONG + U_LONG
ALL_FLOATS = DOUBLE + FLOAT


#Data file specific legal data types for related data

NUMPY_DTYPES = BOOL + BYTE + U_BYTE + SHORT + U_SHORT + INTEGER + U_INTEGER + LONG +\
U_LONG + FLOAT + DOUBLE

NETCDF3_DTYPES = BYTE + SHORT + INTEGER + FLOAT + DOUBLE + STRING

GDAL_DTYPES = BYTE + SHORT + U_SHORT + INTEGER + U_INTEGER + FLOAT + DOUBLE



#_______________________________________________________________________________

class DefaultSettings:
    """Class with default settings for the data interface that can be
    changed by the user by modifying the related XML document with file name
    declared in constant FILENAME_DEFAULT_SETTINGS_XML"""

    def __init__(self):
        """Constructor - Reading related XML file and storing values as attributes in class"""
      
        pDocXml = minidom.parse(FILENAME_DEFAULT_SETTINGS_XML)
        

        #Default settings for data interface functionality
        #-------------------------------------------------------------------------------
        for node_Interface in pDocXml.getElementsByTagName('interface'):

            #Data related settings
            for node_Data in node_Interface.getElementsByTagName('data'):
                self.dataDirectory = str(node_Data.getAttribute('directory')) #DATA_PATH = 'data/'
                self.checkData = str(node_Data.getAttribute('check'))

            #Logger related settings
            for node_Logger in node_Interface.getElementsByTagName('logger'):
                self.loggerFile = str(node_Logger.getAttribute('path')) #FILENAME_INTERFACE_LOGFILE = 'interface.log'
                self.loggerLevelConsole = str(node_Logger.getAttribute('loglevelconsole'))
                self.loggerLevelFile = str(node_Logger.getAttribute('loglevelfile'))

            #Udunits related settings
            for node_Udunits in node_Interface.getElementsByTagName('udunits'):
                self.udunitsXml = str(node_Udunits.getAttribute('path')) #UDUNITS_XML = '/usr/share/xml/udunits/udunits2.xml'
                self.udunitsLib = CDLL(node_Udunits.getAttribute('library')) #UDUNITS_LIB = CDLL("libudunits2.so.0.0.0")


        #Default settings for NetCDF data files
        #-------------------------------------------------------------------------------
        for node_NetCdf in pDocXml.getElementsByTagName('netcdf'):

            #Name of axis default settings (--> Name of dimensions = Name and shape of coordinate variables)
            for node_Axis in node_NetCdf.getElementsByTagName('axis'):
                self.axisTimeName = str(node_Axis.getAttribute('time'))
                self.axisHeightName = str(node_Axis.getAttribute('height'))
                self.axisLatitudeName = str(node_Axis.getAttribute('latitude'))
                self.axisLongitudeName = str(node_Axis.getAttribute('longitude'))

            #Dimension default settings
            for node_Dimension in node_NetCdf.getElementsByTagName('dimension'):
                for node_DimTime in node_Dimension.getElementsByTagName('time'):
                    self.dimTimeIsUnlimited = str(node_DimTime.getAttribute('isUnlimited'))

            #Global attribute default settings
            for node_Attribute in node_NetCdf.getElementsByTagName('attribute'):
                if node_Attribute.parentNode.nodeName == 'netcdf':
                    self.attrConventions = str(node_Attribute.getAttribute('Conventions')) 
                    self.attrInstitution = str(node_Attribute.getAttribute('institution')) #MODEL_REFERENCE_INSTITUTION = "LSiiT, University of Strasbourg, France"

            #Variable default settings
            for node_Variable in node_NetCdf.getElementsByTagName('variable'):
                for node_VarTime in node_Variable.getElementsByTagName('time'):
                    self.varTimeType = str(node_VarTime.getAttribute('type')) 
                    for node_VarTimeAttribute in node_VarTime.getElementsByTagName('attribute'):
                        self.varTimeAttrUnits = str(node_VarTimeAttribute.getAttribute('units')) 
                        self.varTimeAttrCalendar = str(node_VarTimeAttribute.getAttribute('calendar')) #MODEL_REFERENCE_CALENDAR = 'gregorian'
################!!! Type for 'height', 'latitude' and 'longitude' changed from float to double due to problems
                for node_VarHeight in node_Variable.getElementsByTagName('height'):
                    self.varHeightType = str(node_VarHeight.getAttribute('type')) 
                    for node_VarHeightAttribute in node_VarHeight.getElementsByTagName('attribute'):
                        self.varHeightAttrPositive = str(node_VarHeightAttribute.getAttribute('positive')) 

                for node_VarLatitude in node_Variable.getElementsByTagName('latitude'):
                    self.varLatitudeType = str(node_VarLatitude.getAttribute('type')) 
                    for node_VarLatitudeAttribute in node_VarLatitude.getElementsByTagName('attribute'):
                        self.varLatitudeAttrUnits = str(node_VarLatitudeAttribute.getAttribute('units')) 

                for node_VarLongitude in node_Variable.getElementsByTagName('longitude'):
                    self.varLongitudeType = str(node_VarLongitude.getAttribute('type'))
                    for node_VarLongitudeAttribute in node_VarLongitude.getElementsByTagName('attribute'):
                        self.varLongitudeAttrUnits = str(node_VarLongitudeAttribute.getAttribute('units')) 


        #def __del__(self):
            #"""Destructor"""



#_______________________________________________________________________________


class LoggingInterface:
    """Class for initialization and destruction of defined loggers using the logging API of Python"""


    def __init__(self, rootName_, logLevelConsole_, logLevelFile_):
        """Constructor

        INPUT_PARAMETERS:
        rootName          - Declares the name that is used in the position of 'root'
        logLevelConsole   - Declares the minimum level that is used by the console handler
        logLevelFile      - Declares the minimum level that is used by the file handler

        COMMENTS:
        The same name as defined here in the argument 'rootName' must be used for all loggers
        of an instance.
        """

        self.pDefaultSettings = DefaultSettings()

        #Get logging levels
        pLogLevelConsole = self.__getLogLevel(logLevelConsole_)
        pLogLevelFile = self.__getLogLevel(logLevelFile_)


        #Initialize Logger
        #-------------------------------------------------------------------------------
        #Create logger
        self.pLogger = logging.getLogger(str(rootName_))
        self.pLogger.setLevel(logging.DEBUG)

        #Create console handler 
        self.pConsoleHandler = logging.StreamHandler()
        self.pConsoleHandler.setLevel(pLogLevelConsole)

        #Create file handler
        self.pFileHandler = logging.FileHandler(self.pDefaultSettings.loggerFile) #FILENAME_INTERFACE_LOGFILE
        self.pFileHandler.setLevel(pLogLevelFile)

        #Define formatter and add to the handlers
        datefmt='%a, %d %b %Y %H:%M:%S'
        formatterFileHandler = logging.Formatter("%(asctime)s %(name)-55s %(levelname)-8s %(message)s", datefmt)
        formatterConsoleHandler = logging.Formatter("%(levelname)-8s - %(message)s", datefmt)
        self.pFileHandler.setFormatter(formatterFileHandler)
        self.pConsoleHandler.setFormatter(formatterConsoleHandler)

        #Attach handlers to logger
        self.pLogger.addHandler(self.pFileHandler)
        self.pLogger.addHandler(self.pConsoleHandler)


    def __del__ (self):
        """Destructor"""

        #Flush and close handlers, shutdown logging
        self.pLogger.removeHandler(self.pConsoleHandler)
        self.pLogger.removeHandler(self.pFileHandler)
        logging.shutdown()


    def __getLogLevel(self, logLevel_):
        """Return logging level depending on input string"""

        if logLevel_ == 'debug':
            pLogLevel = logging.DEBUG
        elif logLevel_ == 'info':
            pLogLevel = logging.INFO
        elif logLevel_ == 'warning':
            pLogLevel = logging.WARNING
        elif logLevel_ == 'error':
            pLogLevel = logging.ERROR
        elif logLevel_ == 'critical':
            pLogLevel = logging.CRITICAL
        else:
            raise Exception("Error: Logger level '" + str(logLevel_) + "' is not valid!")

        return pLogLevel