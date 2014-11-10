#! /usr/bin/python
# -*- coding: latin1 -*-

"""
Control module for Interface 

This class is containing all possible operations that can be employed within the interface
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-03-28"
__version__ = "v0.1.2"


#Changelog
#-------------------------------------------------------------------------------
#2011-01-05: v0.1.2 logging implemented
#2010-11-22: v0.1.1 comments and docstrings added
#2010-10-08: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
import os
import logging

#related libraries
import numpy

#local applications / library specific import
from interface_Settings import *
from interface_Model import *
from interface_ModelUtilities import *

#===============================================================================



class ControlModel:
    """
    Controlling class for module 'interface_Model' and 'interface_ModelUtilities"
    
    Controlls methods of classes provided by the module 'interface_Model' for different operations.
    List 'pDataList' represents all data of the internal model.
    """


    def __init__(self, infile_, option_):
        """
        Constructor for new control instance of specific file.

        INPUT_PARAMETERS:
        infile      - name of datafile without suffixes (string)
        option      - Parser.options arguments

        COMMENTS:
        Suffixes will be automatically assigned and must respect the declarations
        in the module 'interface_Settings'.
        """
        
        self.startTime = time.time()

        infile = str(infile_).rsplit('__',1)
        infileName = infile[0]
        self.inputFile = infileName #old: DATA_PATH+infileName
        self.pDataList = list() #Complete list of data containing pDimList, pAttrList, pVarList

        self.pProcessingTool = ProcessingTool()

        self.pParserOptions = option_ #Parser
        
        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)
        self.pLogger.info("---------------------------------------------------------------------------------------------")
        self.pLogger.info("Open project '" + self.inputFile + "':")


    def __del__(self):
        """Destructor"""
        #del self.pDataList
        self.pLogger.info("Close project '" + self.inputFile + "'. Project processing time [s]: '" + str(time.time() - self.startTime) + "'.")
        self.pLogger.info("---------------------------------------------------------------------------------------------")
      

    def readMetadataNcml(self):
        """Read metadata from NCML XML file and append data to list of internal model:
        Dimensions, attributes, variables."""

        pDocNcml = ModelMetadataNcmlRead(self.inputFile)

        pDimList = pDocNcml.readDimensions()
        self.pDataList.append(pDimList)
        pAttrList = pDocNcml.readGlobalAttributes()
        self.pDataList.append(pAttrList)
        pVarList = pDocNcml.readVariables()
        self.pDataList.append(pVarList)

        return


    def readDataNumpy(self):
        """
        Read data from numpy array and coordinate metadata file and attach data to variables of internal model.
        Check finally data model if it is correct.

        COMMENT:
        The numpy array and the coordinate metadata file can be read after the data list
        was created by the function 'readMetadataNcml' (Meaning and internal model is already
        existing).
        To each data variable data will be attached from the numpy array and to each coordinate variable
        coordinate values will be attached from the calculated values derived form the coordinate
        metatadata file. Afterwards a consistency check of the internal data model is employed.
        The numpy array can have the following shapes:
        
        (variable, time, z, lat, lon)   - ndim == 5 considered as grid data (multiple values for z, lat, lon)
        (time, variable)                - ndim == 2 considered as station data (single value for z, lat, lon)

        IMPORTANT:
        - the number of time, z, lat and lon values must be the same as defined by the dimensions of
            the NCML metadata file.
        - The shape of the variable dimension in the numpy array must represent the same number as the
            number of variables defined in the NCML metadata file.
        - The variable order in the numpy array must be the same as the order of variables
            appearing in the NCML metadata file (first to last). Otherwise data will be allocated to a wrong variable.
        """

        #Get correct inherited class of ModelDataRead
        #-------------------------------------------------------------------------------
        if os.path.exists(self.inputFile+FILENAME_SUFFIX_NUMPYDATA):
            pNumpy = numpy.load(self.inputFile+FILENAME_SUFFIX_NUMPYDATA)

            if pNumpy.ndim == 2: #(time, variable) considered as station data
                self.pDataModel = ModelDataStationRead(self.inputFile)

                #append suffix '_time_series' to filename if not part of filename string
                self.inputFile = self.pProcessingTool.checkDapperTimeSeriesFilename(self.inputFile)

            elif pNumpy.ndim == 5: #(variable, time, z, lat, lon) considered as grid data
                self.pDataModel = ModelDataGridRead(self.inputFile)

            else:
                raise Exception("Error: Data file '" + str(self.inputFile+FILENAME_SUFFIX_NUMPYDATA) +  "' with '" + \
                str(pNumpy.ndim) + "' dimensions can't be read. Allowed and defined are '5' (grid data) or '2' (station data) dimensions.")
        else:
            raise Exception("Error: Numpy data file '" + str(self.inputFile+FILENAME_SUFFIX_NUMPYDATA) + "' not found.")


        #Get values for coordinate variables and data variables
        #-------------------------------------------------------------------------------
        pVarList = self.pDataList[2]

        pVarList = self.pDataModel.getCoordinateVariables(pVarList)
        pVarList = self.pDataModel.getDataVariables(pVarList)

        self.pDataList[2] = pVarList #is now the complete data model

        #Check complete data model if it is correct and cosistent
        #-------------------------------------------------------------------------------
        if self.pDataModel.checkDataModel(self.pDataList) == False: #if error occured
            self.pLogger.error("Summary: Data model consistency check failed. See error messages above.")
            #exit()

        return


    def readNetCdf(self):
        """Read one or multiple NetCDF files and save data in internal model"""

        pDocNetCdf = ModelNetCdfRead(self.inputFile)

        pDimList = pDocNetCdf.readDimensions()
        self.pDataList.append(pDimList)
        pAttrList = pDocNetCdf.readGlobalAttributes()
        self.pDataList.append(pAttrList)
        pVarList = pDocNetCdf.readVariables()
        self.pDataList.append(pVarList)

        return


    def printModel(self):
        """Print elements of internal data model on screen, according to settings of Parser"""

        if self.pParserOptions.printMeta or self.pParserOptions.printCoords or self.pParserOptions.printVars:
            pModelPrint = ModelPrint(self.pDataList)
            if self.pParserOptions.printMeta: #Print metadata of internal model (dimensions, attributes, variables)
                pModelPrint.printDimensions()
                pModelPrint.printGlobalAttributes()
                pModelPrint.printVariables()
            if self.pParserOptions.printCoords: #Print coordinate variables of internal model
                pModelPrint.printCoordinateVariablesData()
            if self.pParserOptions.printVars: #Print data variables of internal model
                pModelPrint.printDataVariablesData()
        else:
             self.pLogger.info("Set parser options [-m] [-c] [-v] if you want to print internal data model")
  
        return


    def checkNetCdf(self):
        """Checks if a NetCDF file is conform to a convention. Depending on the convention check,
        either an external NetCDF file or a NetCDF file present in the internal data model is needed for the check"""

        if self.pParserOptions.checkNetCdf in ['','cf','default','station','cf+default','cf+default+station'] :
            NetCdfChecker = ModelCheckNetCdf(self.inputFile, self.pDataList)

            #Check for CF Convention
            #-------------------------------------------------------------------------------
            if 'cf' in self.pParserOptions.checkNetCdf:
                errorStatus = NetCdfChecker.checkCf()
                if errorStatus > 0: #> 0 --> Number of errors that occured;
                    self.pLogger.error("CFChecker detected '" + str(errorStatus) +  "' errors for file '" + str(self.inputFile) + \
                    "', so it can not be considered as a valid CF file! Check error messages on the screen (They are not saved in the logfile)!")
                elif errorStatus < 0: #< 0 --> -Number of warnings that occured (no errors occured)
                    self.pLogger.warning("CFChecker detected '" + str(-(errorStatus)) + "' warnings for file '" + str(self.inputFile) + \
                    "'. Check warning messages on the screen (They are not saved in the logfile)!")
                    self.pLogger.info("CFChecker detected no errors for file '" + str(self.inputFile) + "', so it can be considered as valid CF file.")
                else: #== 0 --> No errors and warnings occured
                    self.pLogger.info("CFChecker detected no errors for file '" + str(self.inputFile) + "', so it can be considered as valid CF file.")

            #Check if default settings are observed as defined in related XML file
            #-------------------------------------------------------------------------------
            if 'default' in self.pParserOptions.checkNetCdf: 
                if NetCdfChecker.checkDefaultSettings() == True: #No error detected
                    self.pLogger.info("'Default settings comparision check' for NetCdf file '" + str(self.inputFile) + "' was successfull. No errors found.")
                else: #Error detected
                    self.pLogger.error("Summary: 'Default settings comparision check' for NetCdf file '" + str(self.inputFile) + "' failed. See error messages above.")

            #Check for Dapper In-situ Data Convention for time series station data
            #-------------------------------------------------------------------------------
            if 'station' in self.pParserOptions.checkNetCdf:
                if NetCdfChecker.checkStation() == True: #No error detected
                    self.pLogger.info("'Dapper In-situ Data Convention' check for NetCdf file '" + str(self.inputFile) + "' was successfull. No errors found.")
                else: #Error detected
                    self.pLogger.error("Summary: 'Dapper In-situ Data Convention' check for NetCdf file '" + str(self.inputFile) + "' failed. See error messages above.")
        else:
            self.pLogger.info("Set parser option [-f] with allowed choices if you want to check a NetCDF file convention")

        return


    def writeMetadataNcml(self):
        """Create NCML metadata file out of internal model"""

        pDimList = self.pDataList[0]
        pAttrList = self.pDataList[1]
        pVarList = self.pDataList[2]

        pDocNcml = ModelMetadataNcmlWrite(self.inputFile)
                  
        pDocNcml.addDimensions(pDimList)
        pDocNcml.addGlobalAttributes(pAttrList)
        pDocNcml.addVariables(pVarList)

        #pDocNcml.printNcmlOnScreen()

        return


    def writeDataNumpy(self):
        """Create numpy data array and coordinate metadata file out of internal model"""

        pVarList = self.pDataList[2]

        pDataModel = ModelDataWrite(self.inputFile)
        pDataModel.writeCoordinateVariables(pVarList)
        pDataModel.writeDataVariables(pVarList)
    
        return


    def writeNetCdf(self):
        """Write NetCDF file out of internal model"""

        pDimList = self.pDataList[0]
        pAttrList = self.pDataList[1]
        pVarList = self.pDataList[2]

        pDocNetCdf = ModelNetCdfWrite(self.inputFile)

        pDocNetCdf.writeDimensions(pDimList)
        pDocNetCdf.writeGlobalAttributes(pAttrList)
        pDocNetCdf.writeVariables(pVarList)

        return


#-------------------------------------------------------------------------------


    def makeNumpyVarBool(self):
        """Change values of a variable of a choosen variable number (variable index number of numpy data
        array) to booleans by excluding values in string pBadValuesListFloat.
        Create for each number a new variable and adapt metadata. Export new data model"""

        #Get values from parser
        #-------------------------------------------------------------------------------
        modelBoolParser = self.pParserOptions.makeBool
        varNr = int(modelBoolParser[0]) #Data variable number that's value should be extracted

        badValuesString = modelBoolParser[1] #String with bad values that are to be excluded
        #String from parser needs to be changed to a list (of strings)
        pBadValuesListString = self.pProcessingTool.string2List(badValuesString, ',')
        if not 'None' in pBadValuesListString: #If values should be excluded
            #String values in list are converted to float values
            pBadValuesListFloat = [float(i) for i in pBadValuesListString]
        else: #if no values should be excluded
            pBadValuesListFloat = []


        #Convert Numpy variable to boolean
        #-------------------------------------------------------------------------------
        pNumpyData = ModelData2Bool(self.inputFile)

        pNumpyData.changeVar2BoolVars(varNr, pBadValuesListFloat)
        pNumpyData.writeNumpyData()
        pNumpyData.writeMetadataNcml()
        pNumpyData.completeMetadataNcml()

        return
       

