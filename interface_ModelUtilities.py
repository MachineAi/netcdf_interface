#! /usr/bin/python
# -*- coding: latin1 -*-

"""
ModelUtilities module for Interface.

This module contains utility classes to employ additional operations that are related
to the data interface. It is controlled by
the class 'ControlModel' of the module 'interface_Control'
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-03-28"
__version__ = "v0.1.2"


#Changelog
#-------------------------------------------------------------------------------
#2011-01-14: v0.1.2 logging implemented, functionalities changed
#2010-11-23: v0.1.1 comments and docstrings added
#2010-10-08: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
import logging

#related libraries
import numpy

#local applications / library specific import
from interface_Settings import *
from interface_ProcessingTools import *
from etc.progressBar import * #needs empty '__init__.py' file in directory
from etc.cfchecks import startCfChecksFromInterface #needs empty '__init__.py' file in directory

#===============================================================================



class ModelCheckNetCdf:
    """Class with functions to check if a NetCdf file is conform to a specific convention"""


    def __init__(self, infile_, pDataList_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - Name of NetCDF file name to check with or without suffix (string)
        DataList      - The complete interal data model list
        """
        
        #Initalization
        #-------------------------------------------------------------------------------
        self.netCdfName = str(infile_)
        if not self.netCdfName.endswith(FILENAME_SUFFIX_NETCDF): #Add filename suffix '.nc' if this is missing
            self.netCdfName = self.netCdfName + FILENAME_SUFFIX_NETCDF

        self.pDimList = pDataList_[0]
        self.pAttrList = pDataList_[1]
        self.pVarList = pDataList_[2]

        self.pProcessingTool = ProcessingTool()
        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)
       

    #def __del__ (self):
        #"""Destructor"""


    def checkCf(self):
        """
        Check if a NetCDF file is conform to the CF Convention.
        
        Use of Program 'cfchecker 2.0.2' written by Rosalyn Hatcher (Met Office, UK)
        that was adapted with different settings and the function 'startCfChecksFromInterface'
        so that it can be started from this interface.
        """

        #'cfchecker'-program is in directory '/etc', but is startet from interface with its path
        return startCfChecksFromInterface(self.netCdfName) #start cfchecks program


    def checkDefaultSettings(self):
        """
        Check if a NetCDF file is conform to the default settings

        This function compares a NetCDF file (present in the internal data model) with the
        default settings as they are defined in the function 'pDefaultSettings". The default
        settings in this function are declared in the related XML file. This function assumes that the internal
        data model was defined consistent by the interface consistency check that was employed
        when loading data of the data model.
        """
               
        pDefaultSettings = DefaultSettings()
        netCdfOk = True #Error flag, gets 'False' if on or more errors were found
      

        #Dimensions
        #-------------------------------------------------------------------------------
        for pDim in self.pDimList[:]:
         
            if pDim.getName() in TIME:

                #Check that same dimension name is used as the axis name that is defined in the XML settings file
                if str(pDim.getName()) != str(pDefaultSettings.axisTimeName):
                    self.pLogger.error("Dimension name '" + str(pDim.getName()) + "' is not the same as the default axis name '" + \
                    str(pDefaultSettings.axisTimeName) + "'.")
                    netCdfOk = False

                #Compare 'isUnlimted'-attribute of dimension 'time'
                if str(pDim.getIsUnlimited()) != str(self.pProcessingTool.convertBool(pDefaultSettings.dimTimeIsUnlimited)):
                    self.pLogger.error("'" + str(pDim.getName()) + "' dimension attribute 'isUnlimited' is set to '" + str(pDim.getIsUnlimited()) + \
                    "' in NetCDF file, but default value is '" + str(self.pProcessingTool.convertBool(pDefaultSettings.dimTimeIsUnlimited)) + "'.")
                    netCdfOk = False

            if pDim.getName() in HEIGHT:

                #Check that same dimension name is used as the axis name that is defined in the XML settings file
                if str(pDim.getName()) != str(pDefaultSettings.axisHeightName):
                    self.pLogger.error("Dimension name '" + str(pDim.getName()) + "' is not the same as the default axis name '" + \
                    str(pDefaultSettings.axisHeightName) + "'.")
                    netCdfOk = False

            if pDim.getName() in LATITUDE:

                #Check that same dimension name is used as the axis name that is defined in the XML settings file
                if str(pDim.getName()) != str(pDefaultSettings.axisLatitudeName):
                    self.pLogger.error("Dimension name '" + str(pDim.getName()) + "' is not the same as the default axis name '" + \
                    str(pDefaultSettings.axisLatitudeName) + "'.")
                    netCdfOk = False

            if pDim.getName() in LONGITUDE:

                #Check that same dimension name is used as the axis name that is defined in the XML settings file
                if str(pDim.getName()) != str(pDefaultSettings.axisLongitudeName):
                    self.pLogger.error("Dimension name '" + str(pDim.getName()) + "' is not the same as the default axis name '" + \
                    str(pDefaultSettings.axisLongitudeName) + "'.")
                    netCdfOk = False


        #Global attributes
        #-------------------------------------------------------------------------------
        attrConvCheck = attrInstCheck = 0
        for pAttr in self.pAttrList[:]:

            #Compare global attribute "Conventions"
            if pAttr.getName() == "Conventions":
                attrConvCheck = attrConvCheck + 1
                if str(pAttr.getValue()) != str(pDefaultSettings.attrConventions):
                    self.pLogger.error("Global attribute '" + str(pAttr.getName()) + "' is set to '" + str(pAttr.getValue()) + \
                    "' in NetCDF file, but default value is '" + str(pDefaultSettings.attrConventions) + "'.")
                    netCdfOk = False

            #Compare global attribute "institution"
            if pAttr.getName() == "institution":
                attrInstCheck = attrInstCheck + 1
                if str(pAttr.getValue()) != str(pDefaultSettings.attrInstitution):
                    self.pLogger.error("Global attribute '" + str(pAttr.getName()) + "' is set to '" + str(pAttr.getValue()) + \
                    "' in NetCDF file, but default value is '" + str(pDefaultSettings.attrInstitution) + "'.")
                    netCdfOk = False

        #Exactly one global attribute with name 'Conventions' must have been found
        if attrConvCheck != 1:
            self.pLogger.error("Found '" + str(attrConvCheck) + "' global attribute 'Conventions' in NetCDF file. One attribute is necessary")
            netCdfOk = False

        #Exactly one global attribute with name 'institution' must have been found
        if attrInstCheck != 1:
            self.pLogger.error("Found '" + str(attrInstCheck) + "' global attribute 'institution' in NetCDF file. One attribute is necessary")
            netCdfOk = False


        #Variables
        #-------------------------------------------------------------------------------
        for pVar in self.pVarList[:]:

            if pVar.getName() in TIME:

                #Check that same variable name and shape name is used as the axis name that is defined in the XML settings file
                if (str(pVar.getName()) != str(pDefaultSettings.axisTimeName)) or (str(pVar.getShape()) != str(pDefaultSettings.axisTimeName)):
                    self.pLogger.error("Coordiante variable name '" + str(pVar.getName()) + "' or variable shape '" + str(pVar.getShape()) + \
                    "'is not the same as the default axis name '" + str(pDefaultSettings.axisTimeName) + "'.")
                    netCdfOk = False

                #Compare type of variable 'time'
                if str(self.pProcessingTool.dataType_2NetCdf(pVar.getType())) != str(self.pProcessingTool.dataType_2NetCdf(pDefaultSettings.varTimeType)):
                    self.pLogger.error("Variable '" + str(pVar.getName()) + "' is of type '" + str(pVar.getType()) + \
                    "' in NetCDF file, but default value is '" + str(pDefaultSettings.varTimeType) + "'.")
                    netCdfOk = False

                for pVarAttr in pVar.getAttributes():
                    #Compare attribute 'units'
                    if pVarAttr.getName() == "units" and str(pVarAttr.getValue()) != str(pDefaultSettings.varTimeAttrUnits):
                        self.pLogger.error("Global attribute '" + str(pVarAttr.getName()) + "' is set to '" + str(pVarAttr.getValue()) + \
                        "' in NetCDF file, but default value is '" + str(pDefaultSettings.varTimeAttrUnits) + "'.")
                        netCdfOk = False
                    #Compare attribute 'calendar'
                    if pVarAttr.getName() == "calendar" and str(pVarAttr.getValue()) != str(pDefaultSettings.varTimeAttrCalendar):
                        self.pLogger.error("Global attribute '" + str(pVarAttr.getName()) + "' is set to '" + str(pVarAttr.getValue()) + \
                        "' in NetCDF file, but default value is '" + str(pDefaultSettings.varTimeAttrCalendar) + "'.")
                        netCdfOk = False

            if pVar.getName() in HEIGHT:

                #Check that same variable name and shape name is used as the axis name that is defined in the XML settings file
                if (str(pVar.getName()) != str(pDefaultSettings.axisHeightName)) or (str(pVar.getShape()) != str(pDefaultSettings.axisHeightName)):
                    self.pLogger.error("Coordiante variable name '" + str(pVar.getName()) + "' or variable shape '" + str(pVar.getShape()) + \
                    "'is not the same as the default axis name '" + str(pDefaultSettings.axisHeightName) + "'.")
                    netCdfOk = False

                #Compare type of variable 'height'
                if str(self.pProcessingTool.dataType_2NetCdf(pVar.getType())) != str(self.pProcessingTool.dataType_2NetCdf(pDefaultSettings.varHeightType)):
                    self.pLogger.error("Variable '" + str(pVar.getName()) + "' is of type '" + str(pVar.getType()) + \
                    "' in NetCDF file, but default value is '" + str(pDefaultSettings.varHeightType) + "'.")
                    netCdfOk = False

                for pVarAttr in pVar.getAttributes():
                    #Compare attribute 'positive'
                    if pVarAttr.getName() == "positive" and str(pVarAttr.getValue()) != str(pDefaultSettings.varHeightAttrPositive):
                        self.pLogger.error("Global attribute '" + str(pVarAttr.getName()) + "' is set to '" + str(pVarAttr.getValue()) + \
                        "' in NetCDF file, but default value is '" + str(pDefaultSettings.varHeightAttrPositive) + "'.")
                        netCdfOk = False

            if pVar.getName() in LATITUDE:

                #Check that same variable name and shape name is used as the axis name that is defined in the XML settings file
                if (str(pVar.getName()) != str(pDefaultSettings.axisLatitudeName)) or (str(pVar.getShape()) != str(pDefaultSettings.axisLatitudeName)):
                    self.pLogger.error("Coordiante variable name '" + str(pVar.getName()) + "' or variable shape '" + str(pVar.getShape()) + \
                    "'is not the same as the default axis name '" + str(pDefaultSettings.axisLatitudeName) + "'.")
                    netCdfOk = False

                #Compare type of variable 'latitude'
                if str(self.pProcessingTool.dataType_2NetCdf(pVar.getType())) != str(self.pProcessingTool.dataType_2NetCdf(pDefaultSettings.varLatitudeType)):
                    self.pLogger.error("Variable '" + str(pVar.getName()) + "' is of type '" + str(pVar.getType()) + \
                    "' in NetCDF file, but default value is '" + str(pDefaultSettings.varLatitudeType) + "'.")
                    netCdfOk = False

                for pVarAttr in pVar.getAttributes():
                    #Compare attribute 'units'
                    if pVarAttr.getName() == "units" and str(pVarAttr.getValue()) != str(pDefaultSettings.varLatitudeAttrUnits):
                        self.pLogger.error("Global attribute '" + str(pVarAttr.getName()) + "' is set to '" + str(pVarAttr.getValue()) + \
                        "' in NetCDF file, but default value is '" + str(pDefaultSettings.varLatitudeAttrUnits) + "'.")
                        netCdfOk = False

            if pVar.getName() in LONGITUDE:

                #Check that same variable name and shape name is used as the axis name that is defined in the XML settings file
                if (str(pVar.getName()) != str(pDefaultSettings.axisLongitudeName)) or (str(pVar.getShape()) != str(pDefaultSettings.axisLongitudeName)):
                    self.pLogger.error("Coordiante variable name '" + str(pVar.getName()) + "' or variable shape '" + str(pVar.getShape()) + \
                    "'is not the same as the default axis name '" + str(pDefaultSettings.axisLongitudeName) + "'.")
                    netCdfOk = False

                #Compare type of variable 'longitude'
                if str(self.pProcessingTool.dataType_2NetCdf(pVar.getType())) != str(self.pProcessingTool.dataType_2NetCdf(pDefaultSettings.varLongitudeType)):
                    self.pLogger.error("Variable '" + str(pVar.getName()) + "' is of type '" + str(pVar.getType()) + \
                    "' in NetCDF file, but default value is '" + str(pDefaultSettings.varLongitudeType) + "'.")
                    netCdfOk = False

                for pVarAttr in pVar.getAttributes():
                    #Compare attribute 'units'
                    if pVarAttr.getName() == "units" and str(pVarAttr.getValue()) != str(pDefaultSettings.varLongitudeAttrUnits):
                        self.pLogger.error("Global attribute '" + str(pVarAttr.getName()) + "' is set to '" + str(pVarAttr.getValue()) + \
                        "' in NetCDF file, but default value is '" + str(pDefaultSettings.varLongitudeAttrUnits) + "'.")
                        netCdfOk = False

        return netCdfOk


    def checkStation(self):
        """
        Check for Dapper In-situ Data Convention for time series station data

        This function checks if a NetCDF file (present in the internal data model) respects
        the Dapper In-Situ Data Conventions, here for time series of station data. This
        convention must be respected in case that a NetCDF file should be loaded to a Dapper
        dataset by the use of the dapperload programm. Every data variable (not coordinate variable)
        must previously be declared as CF conform. This function assumes that the internal
        data model was defined consistent by the interface consistency check that was employed
        when loading data of the data model.
        """

        netCdfOk = True #Error flag, gets 'False' if on or more errors were found


        #Check NetCdf file name suffix
        #-------------------------------------------------------------------------------

        #NetCdf file as well as Dapper dataset must have filename suffix '_time_series.nc'!
        if not self.netCdfName.endswith(DECLARATION_NETCDF_STATION + FILENAME_SUFFIX_NETCDF): #without filename suffix!
            self.pLogger.warning("Filename '" + str(self.netCdfName) + "' needs to end with the string '" + \
            str(DECLARATION_NETCDF_STATION + FILENAME_SUFFIX_NETCDF) + \
            "' so that it can be considered by Dapper as an in-situ time series dataset. Without this string it will be considered as profile dataset!")
          

        #Dimensions
        #-------------------------------------------------------------------------------
        for pDim in self.pDimList[:]:

####################TEMPORARILY UNLIMITED (for MFDataset), but must obviously be limited for Dapper
            #Obviously 'time' dimension can't be of unlimited size
            #if pDim.getName() in TIME and str(pDim.getIsUnlimited()) != str(self.pProcessingTool.convertBool(False)):
            #    self.pLogger.error("The 'time' dimension needs obviously be of a limited size. Got value '" + str(pDim.getIsUnlimited()) + "' for attribute 'isUnlimited'.")
            #    netCdfOk = False

            #Dimension 'height' needs to to be named 'elev' due to a glitch in the dapperload program
            if pDim.getName() in HEIGHT and pDim.getName() != 'elev':
                self.pLogger.error("The 'height' dimension needs to be named 'elev' for the dapperload program. Got name '" + str(pDim.getName()) + "' instead.")
                netCdfOk = False

            #Dimensions 'height', 'latitude' and 'longitude' must be scalar (of length '1'), since they represents a time
            #series data of a station (for profile: dimension time = '1', height = variant)
            if (pDim.getName() in HEIGHT and pDim.getLength() != 1) or \
            (pDim.getName() in LATITUDE and pDim.getLength() != 1) or \
            (pDim.getName() in LONGITUDE and pDim.getLength() != 1):
                self.pLogger.error("The dimensions 'elev', 'latitude' and 'longitude' need to be of length '1'. Got length '" + \
                str(pDim.getLength()) + "' for dimension '" + str(pDim.getName()) + "' instead.")
                netCdfOk = False


        #Global attributes
        #-------------------------------------------------------------------------------

        for pAttr in self.pAttrList[:]:
            #Compare global attribute 'Conventions' that must be set to 'CF-1.4, epic-insitu-1.0'
            if pAttr.getName() == "Conventions" and pAttr.getValue() != str('CF-1.4, epic-insitu-1.0'):
                self.pLogger.error("The global attribute 'Conventions' needs to have the value 'CF-1.4, epic-insitu-1.0'. Got value '"\
                + str(pAttr.getValue()) + "' instead.")
                netCdfOk = False


        #Variables
        #-------------------------------------------------------------------------------
        varIdCheck = coordAttrCheck = dataVar = 0 #Initialization: Number of data variables
        dataVarTypeFloat = dataVarTypeDouble = coordVarTypeFloat = coordVarTypeDouble = 0 #Initialization: Number of flag which variable type is used

        for pVar in self.pVarList[:]:
        
            #Coordinate variable 'height' needs to to be named 'elev' with shape 'elev' due to a glitch in the dapperload program
            if pVar.getName() in HEIGHT and (pVar.getName() != 'elev' or pVar.getShape() != 'elev'):
                self.pLogger.error("The name and shape of the 'height' coordiante variable needs to be named 'elev' for the dapperload program. Got name '" \
                + str(pVar.getName()) + "' and shape '" + str(pVar.getShape()) + "' instead.")
                netCdfOk = False
                   
            if pVar.getName() in TIME:
                #The 'time' coordinate variable must always be of the type 'float64'
                if pVar.getType() not in DOUBLE:
                    self.pLogger.error("The coordinate variable 'time' must be of type 'double'. Got type '" \
                    + str(pVar.getType()) + "' for coordinate variable '" + str(pVar.getName()) + "' instead.")
                    netCdfOk = False

                #Time unit 'milliseconds since 1970-01-01 00:00:0.0' is recommended by Dapper
                for pVarAttr in pVar.getAttributes():
                    if pVarAttr.getName() == 'units' and pVarAttr.getValue() !=  str('milliseconds since 1970-01-01 00:00:0.0'):
                        self.pLogger.warning("The 'units' attribute for the variable 'time' is recommended to be 'milliseconds since 1970-01-01 00:00:0.0'. Got value '" \
                        + str(pVarAttr.getValue() + "' instead."))


            #The 'elev', 'latitude' and 'longitude' coordinate variables must be of the type 'float32' or 'float64'. They all must be of the same type.
            if (pVar.getName() in HEIGHT or pVar.getName() in LATITUDE or pVar.getName() in LONGITUDE):
                if pVar.getType() in FLOAT:
                    coordVarTypeFloat = coordVarTypeFloat + 1
                elif pVar.getType() in DOUBLE:
                    coordVarTypeDouble = coordVarTypeDouble + 1
                else:
                    self.pLogger.error("The coordinate variables 'elev', 'latitude' and 'longitude' must either be of type 'float32' or 'double'. Got type '" \
                    + str(pVar.getType()) + "' for coordinate variable '" + str(pVar.getName()) + "' instead.")
                    netCdfOk = False

            #Scalar variable with name ID of type 'int32' and with a unique value for each entry of outer sequence is necessary
            if pVar.getName() in ID:
                varIdCheck = varIdCheck + 1
                if (str(pVar.getType()) not in INTEGER) or (str(pVar.getShape()) != ''):
                    self.pLogger.error("A scalar variable that is named '" + str(ID) + "' and that is of type 'int32' with unique values for each entry of the outer sequence is necessary. Got type '" \
                    + str(pVar.getType()) + "' and shape '" + str(pVar.getShape()) + "' for this variable with name '" + str(pVar.getName()) + "' instead.")
                    netCdfOk = False


            #Check data variables
            if pVar.getName() not in COORD_KEYWORDS:
                dataVar = dataVar + 1

                #All data variables must either be of type 'float32' or 'double'. They should all be of the same type
                if pVar.getType() in FLOAT:
                    dataVarTypeFloat = dataVarTypeFloat + 1
                elif pVar.getType() in DOUBLE:
                    dataVarTypeDouble = dataVarTypeDouble + 1
                else:
                    self.pLogger.error("All data variables must either be of type 'float32' or 'double'. Got type '" \
                    + str(pVar.getType()) + "' for data variable '" + str(pVar.getName()) + "' instead.")
                    netCdfOk = False

                for pVarAttr in pVar.getAttributes():

                    #All data variables must have coordinates attributes in the form of 'time elev latitude longitude'.
                    if pVarAttr.getName() == 'coordinates':
                        coordAttrCheck = coordAttrCheck + 1
                        pCoordinatesList = self.pProcessingTool.string2List(pVarAttr.getValue(), ' ')
                        if (pCoordinatesList[0] not in TIME) or (pCoordinatesList[1] != 'elev') or \
                        (pCoordinatesList[2] not in LATITUDE) or (pCoordinatesList[3] not in LONGITUDE):
                            self.pLogger.error("All data variables must have 'coordinates' attributes in the form of 'time elev latitude longitude'. Got value '" \
                            + str(pVarAttr.getValue()) + "' for data variable '" + str(pVar.getName()) + "'.")
                            netCdfOk = False


        #Exactly one variable with name ID must have been found
        if varIdCheck != 1:
            self.pLogger.error("A scalar variable named '" + str(ID) + "' of type 'int32' with unique values for each entry of the outer sequence is necessary. Found '" \
            + str(varIdCheck) + "' variables with this name.")
            netCdfOk = False

        #Each data variable must have a 'coordinates' attribute attached (number of data variables = number of coordinate attributes)
        if coordAttrCheck != dataVar:
            self.pLogger.error("All Data variables must have 'coordinates' attributes in the form of 'time elev latitude longitude'. Found '" \
            + str(dataVar) + "' data variables, but '" + str(coordAttrCheck) + "' data variables with 'coordinates' attributes.")
            netCdfOk = False

        #The 'elev', 'latitude' and 'longitude' coordinate variables must be of the type 'float32' or 'float64'. They all must be of the same type
        if not ((coordVarTypeFloat != 0 and coordVarTypeDouble == 0) or (coordVarTypeFloat == 0 and coordVarTypeDouble != 0)): #(coordVarTypeFloat != coordVarTypeDouble):
            self.pLogger.error("The coordinate variables 'elev', 'latitude' and 'longitude' must all be of the same type that is either 'float32' or 'double'. This is not the case for this file '" \
            + str(self.netCdfName) + "'. Found '" + str(coordVarTypeFloat) + "' coordinate variables of type 'float32' and '" + str(coordVarTypeDouble) + "' of type 'double'.")
            netCdfOk = False

        #All data variables should be of the same type that is either 'float32' or 'double'
        if not ((dataVarTypeFloat != 0 and dataVarTypeDouble == 0) or (dataVarTypeFloat == 0 and dataVarTypeDouble != 0)): #(dataVarTypeFloat != dataVarTypeDouble):
            self.pLogger.warning("All data variables should be of the same type that is either 'float32' or 'double'. This is not the case for this file '" \
            + str(self.netCdfName) + "'. Found '" + str(dataVarTypeFloat) + "' data variables of type 'float32' and '" + str(dataVarTypeDouble) + "' of type 'double'.")

        return netCdfOk
        


#_______________________________________________________________________________

class ModelData2Bool:
    """This class is designed for converting a data variable with number 'varNr'
    (variable index number of numpy data array) to a new data model with a new boolean
    variable for each value that is part of the data variable. Values in the list
    pBadValuesList are excluded and for this values no new variable will be created"""


    def __init__(self, infile_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - name of data model file name without suffix (string)
        """
        self.pDefaultSettings = DefaultSettings()

        self.numpyDataName = infile_+FILENAME_SUFFIX_NUMPYDATA
        self.ncmlName = infile_+FILENAME_SUFFIX_NCML
        #self.numpymetaName = infile_+FILENAME_SUFFIX_NUMPYXML

        #Use Processing Tools
        self.pProcessingTool = ProcessingTool()
        self.pProcessNcml = ProcessNcml(self.ncmlName)
        #self.pProcessNumpymeta = ProcessNumpymeta(self.numpymetaName)

        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)

        self.pNumpyData = numpy.load(str(self.numpyDataName))


    #def __del__ (self):
        #"""Destructor"""
        

    def changeVar2BoolVars(self, varNr_, pBadValuesList_):
        """
        Change data to boolean

        For a data variable with number 'varNr'  of input numpy data array 'pInNumpy'
        create for each value in this variable a new data variable in a new numpy data array
        that's entries are either true or false, depending if a specific value is existing at this
        position. Values in the list 'pBadValuesList' are excluded. The returning numpy
        array represents true/false values (or '1' and '0') in case that a value existed at this position.
        ! Numpy data type is 'Byte' instead of 'Bool' since the boolean data type does not exist for NetCDF !
        """

        #Get data and settings
        #-------------------------------------------------------------------------------
        self.pLogger.debug("Modify variable # '" + str(varNr_) +  "' to boolean numpy array by excluding the following values: '" + \
        str(pBadValuesList_) + "'. Please wait...")

        pInNumpy =  self.pNumpyData #numpy.load(str(self.numpyDataName))

        dimVarIn = pInNumpy.shape[0] #Number of variables in array

        #dimVarOut = Amount of values between maximum and minimum value expect bad values
        dimVarOut = int(numpy.max(pInNumpy) - numpy.min(pInNumpy) + 1 - len(pBadValuesList_))

        dimT = pInNumpy.shape[1] #Time Dimension
        dimZ = pInNumpy.shape[2] #Height Dimensions
        dimY = pInNumpy.shape[3] #Last but one axis top to bottom: lat -> row
        dimX = pInNumpy.shape[4] #Last axis left to right: lon -> col

        #Output data array
        pNumpyConv = numpy.empty([dimVarOut, dimT, dimZ, dimY, dimX], dtype = numpy.int8)

        #Define progress bar settings
        widgetsBar = ['Conversion status: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
        progressBar = ProgressBar(widgets=widgetsBar, maxval=dimT).start()


        #Get data and settings
        #-------------------------------------------------------------------------------
        if varNr_ < 0 or varNr_ > dimVarIn-1: #If variable number is outside of dimension range
            raise Exception("Error: Argument varNr (value '" + str(varNr_) +  "') is wrong. Argument varNr represents variable number of input data!")
            exit()

        else:
            for i_time in range (0, dimT, 1): #Go trough all times
                dimVarOutNr = 0 #Running number for dimension variable of output numpy array

                #For all values 'i_varOut' in between minimum and maximum of specifc data variable
                for i_varOut in range (int(numpy.min(pInNumpy)), int(numpy.max(pInNumpy))+1, 1):#+1 to read also max value
                    if not i_varOut in pBadValuesList_: #Ignore bad values

                        #If value 'i_varOut' at specific position exists, then save true in output numpy, otherwise false
                        pNumpyConv[dimVarOutNr, i_time, :,:,:] = numpy.where(pInNumpy[varNr_, i_time, :,:,:] == i_varOut, 1, 0)
                        #pNumpyConv[dimVarOutNr, i_time, :,:,:] = numpy.where(pInNumpy[varNr_, i_time, :,:,:] == i_varOut, True, False)
                        dimVarOutNr = dimVarOutNr + 1

                progressBar.update(i_time+1)# Progress bar
      
        self.pNumpyData = pNumpyConv

        return


    def writeNumpyData(self):
        """Export numpy data array to file"""
       
        self.pLogger.debug("Numpy output will be file saved as '" + str(self.numpyDataName) + "'. Please wait...")
        numpy.save(str(self.numpyDataName), self.pNumpyData) #Better as 'tofile'. Also possible: 'dump'
        self.pLogger.debug("Done. Shape of resulting npy-file = '" + str(self.pNumpyData.shape) + "'; Data type: '" + str(self.pNumpyData.dtype) + "'.")

        return
    

    def writeMetadataNcml(self):
        """Create new NCML XML file according to the specifications of the data model and
        complete this file by the metadata that can be extracted out of input metadata"""

        #Get metadata information from file
        #-------------------------------------------------------------------------------
        pNumpyData = self.pNumpyData
        dimVar = pNumpyData.shape[0] #int(1) #Number of variables in array

        #Define progress bar settings
        widgetsBar = ['Creating Ncml metadata file: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
        progressBar = ProgressBar(widgets=widgetsBar, maxval=dimVar).start()

        #Write metadata NCML file
        #-------------------------------------------------------------------------------
        self.pProcessNcml.createMacroNcmlFile()
        self.pProcessNcml.fillNcmlMacroWithNumpy(pNumpyData)

        #Correct and complete entries
        for i_var in range(0,dimVar,1): # otherwise returns list of ints from >= start and < end: 0 .. 10
            varName = 'variable #'+str(i_var)
            self.pProcessNcml.changeLocalAttribute(varName, '_FillValue', 'value', '0')

            progressBar.update(i_var+1)# Progress bar

        return


    #Data specific functions
    #-------------------------------------------------------------------------------

    def completeMetadataNcml(self):
        "Complete missing data in NCML XML file manually"

        self.pProcessNcml.changeGlobalAttribute('title', 'value', 'Waterwatch flood occurrence')
        self.pProcessNcml.changeGlobalAttribute('source', 'value', 'No information available')
        self.pProcessNcml.changeGlobalAttribute('references', 'value', 'No information available')
        self.pProcessNcml.changeGlobalAttribute('comment', 'value', 'No information available')

        self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'units', 'value', '1')
        self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'long_name', 'value', 'level')
###############Define Standard Name!
        #self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'standard_name', 'value', '???')
        self.pProcessNcml.removeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'standard_name')


        self.pProcessNcml.changeVariable('variable #0', 'name', 'nodata')
        self.pProcessNcml.changeLocalAttribute('nodata', 'units', 'value', '1')
        self.pProcessNcml.changeLocalAttribute('nodata', 'long_name', 'value', 'area of no data')
###############Define Standard Name!
        #self.pProcessNcml.changeLocalAttribute('nodata', 'standard_name', 'value', '')
        self.pProcessNcml.removeLocalAttribute('nodata', 'standard_name')

        self.pProcessNcml.changeVariable('variable #1', 'name', 'wet')
        self.pProcessNcml.changeLocalAttribute('wet', 'units', 'value', '1')
        self.pProcessNcml.changeLocalAttribute('wet', 'long_name', 'value', 'wet area (flooded in past or at risk)')
###############Define Standard Name!
        #self.pProcessNcml.changeLocalAttribute('wet', 'standard_name', 'value', '')
        self.pProcessNcml.removeLocalAttribute('wet', 'standard_name')

        self.pProcessNcml.changeVariable('variable #2', 'name', 'flooded')
        self.pProcessNcml.changeLocalAttribute('flooded', 'units', 'value', '1')
        self.pProcessNcml.changeLocalAttribute('flooded', 'long_name', 'value', 'flooded area')
###############Define Standard Name!
        #self.pProcessNcml.changeLocalAttribute('flooded', 'standard_name', 'value', '')
        self.pProcessNcml.removeLocalAttribute('flooded', 'standard_name')

        return