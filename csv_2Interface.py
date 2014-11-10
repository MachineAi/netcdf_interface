#! /usr/bin/python
# -*- coding: latin1 -*-

"""
Converts a CSV point observation dataset to the data model.

Module for reading a CSV table file and exporting it to the data model that is
consisting of the following files: numpy data array, coordinate metadata xml file
and NCML NetCDF XML file.
Data is considered as station, therefore the shape of the output numpy array is:
(time, variable). Find more information in the documentation.
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-04-15"
__version__ = "v0.1.4" #MajorVersion(backward_incompatible).MinorVersion(backward_compatible).Patch(Bug_fixes)


#Changelog
#-------------------------------------------------------------------------------
#2001-04-15: v0.1.4 little changes for NcML attributes
#2011-01-14: v0.1.3 logging implemented, functionalities changed
#2010-12-14: v0.1.2 parser added, functionalities changed
#2010-11-22: v0.1.1 comments and docstrings added
#2010-11-10: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
import sys
import csv #Python integrated API for handling CSV data
from optparse import OptionParser #Parser
import logging

#related libraries
import numpy

#local applications / library specific import
from interface_Settings import *
from interface_ProcessingTools import *
from etc.progressBar import * #needs empty '__init__.py' file in directory

#===============================================================================

#Module constants (Parser)
#-------------------------------------------------------------------------------
USAGE = "%prog [options] operation data\
    \n[options]:\
    \n    type '--help' for more information\
    \n\
    \noperation:\
    \n    - csv2Model      Convert CSV table to data model\
    \n\
    \ndata:\
    \n    Table as CSV file, with or without variable names in first row"

DESCRIPTION= "Conversion tool of CEOP-AEGIS data model for CSV table data considered as station data"
EPILOG = "Author: "+__author__+" (E-mail: "+__author_email__+")"

VERSION = "%prog version "+__version__+" from "+__date__


#Module default values / constants, may be overwritten by OptionParser
#-------------------------------------------------------------------------------
NUMPYDATA_DTYPE = 'float32' #Data type of output numpy array
NODATA = -9999 #Value to be used for missing or no data in CSV file

CSV_DIALECT = 'excel'

MODULE_LOGGER_ROOT = 'csv' #Logger root name



#_______________________________________________________________________________

class ControlModelCsv:
    """Control class for model 'ModelCsvRead'. This class is providing all available functions for reading data"""

    def __init__(self, infile_, option_):
        """
        Constructor for new control instance of specific file.

        INPUT_PARAMETERS:
        infile      - name of data file without filename extension (string)
        option      - Parser.options arguments

        COMMENTS:
        Suffixes will be automatically assigned and must respect the declarations
        in the module 'interface_Settings'.
        """

        infile = str(infile_).rsplit('__',1)
        self.inputFile = infile[0]
        self.pModelCsvRead = ModelCsvRead(self.inputFile)

        self.pParserOptions = option_

        self.pParserOptions = option_
        self.pLogger = logging.getLogger(MODULE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)
        self.pLogger.info("Open project '" + self.inputFile + "':")


    #def __del__(self):
        #"""Desctructor"""


    def writeCsvNumpyData(self):
        """Read CSV file and save data as numpy data array according to the specifications
        of the data interface"""

        #Make a copy of the CSV-file as numpy file (only numeric values)
        pDocCsvNumpy = self.pModelCsvRead.createCsvNumpy(self.pParserOptions.dataType)
        pNumpyData = self.pModelCsvRead.readCsvData(pDocCsvNumpy, \
            self.pParserOptions.nodataValue, self.pParserOptions.isVarName)

        #Optional: Get specific information from Csv-file. Depending on data
        if self.pParserOptions.isSpecificData:
            pNumpyData = self.pModelCsvRead.choseSpecificData(pNumpyData,\
                self.pParserOptions.nodataValue, self.pParserOptions.isVarName)

        #Export data as new numpy file
        self.pModelCsvRead.writeNumpyData(pNumpyData)

        return
    
    
    def writeCsvMetadata(self):
        """Get metadata from the CSV file and write metadata to coordinate metadata file and
        NCML XML file according to the specifications of the data interface. Function
        can be called after function 'writeCsvNumpyData' was executed"""

        self.pModelCsvRead.writeMetadataNcml(self.pParserOptions.nodataValue, self.pParserOptions.isVarName)
        self.pModelCsvRead.writeMetadataNumpymeta()
        return


    #optional
    def completeDataModelManually(self):
        """Complete missing data and metadata manually"""

        self.pModelCsvRead.completeDataVariables()
        self.pModelCsvRead.completeMetadataNcml()
        self.pModelCsvRead.completeMetadataNumpymeta()
        return


#_______________________________________________________________________________

class ModelCsvRead:
    """This class contains functions to handle read operations on CSV data and is controlled by
    the class 'ControlModelCsv'"""


    def __init__(self, infile_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - name of CSV file name with filename extension (string)
        """
        self.pDefaultSettings = DefaultSettings()

        self.csvFileName = infile_ #With file name extension
        infile = self.csvFileName.rsplit('.',1) #without file name extension

        self.pProcessingTool = ProcessingTool()

        #attach string '_time_series' to filename if this is not already the suffix
        outfileName = self.pProcessingTool.checkDapperTimeSeriesFilename(infile[0])

        self.numpyDataName = outfileName+FILENAME_SUFFIX_NUMPYDATA
        self.ncmlName = outfileName+FILENAME_SUFFIX_NCML
        self.numpymetaName = outfileName+FILENAME_SUFFIX_NUMPYXML

        #Use Processing Tools
        self.pProcessNcml = ProcessNcml(self.ncmlName)
        self.pProcessNumpymeta = ProcessNumpymeta(self.numpymetaName)

        self.pLogger = logging.getLogger(MODULE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)
                
        
    #def __del__ (self):
        #"""Destructor"""


    def createCsvNumpy(self, dataType_):
        """Creates a empty numpy array with same shape as CSV file and return this numpy array.
        Argument dataType defines the data type of the resulting numpy array."""

        pDocCsv = self.__openCsvFile()

        #Get shape of CSV-file, so that numpy array can be created
        #Iterate trough all rows and enumerate
        nCsvRows = 0
        for csvRow in pDocCsv:
            nCsvRows = nCsvRows + 1
        nCsvCols = len(csvRow)

        #Second step: Create empty numpy file for reading input data
        pDataType = self.pProcessingTool.dataType_2Numpy(dataType_) #Convert to numpy dtype
        pDocCsvNumpy = numpy.zeros((nCsvRows, nCsvCols), dtype = pDataType)

        self.pLogger.debug("Number of rows found in cvs-file: '" + str(nCsvRows) + "'") #number of rows, e.g. 2493
        self.pLogger.debug("Number of columns found in cvs-file: '" + str(nCsvCols) + "'") #number of columns, e.g. 12
    
        return pDocCsvNumpy


    def readCsvData(self, pDocCsvNumpy_, nodata_, isVarName_):
        """Save data of CSV file to previously created empty numpy array (pDocCsvNumpy).
        Returns numpy array with complete CSV data. Save variable names to variable name
        list if variable names are available"""

        #Get input dataset and define settings
        #-------------------------------------------------------------------------------
     
        if isVarName_: #If variable names in first row
            self.pVarNames = list()

        #Open once again CSV file for reading now data to array
        pDocCsvNumpy = pDocCsvNumpy_
        pDocCsv = self.__openCsvFile()
        pDataType = pDocCsvNumpy.dtype

        #Define progress bar settings
        widgetsBar = ['Import status: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
        progressBar = ProgressBar(widgets=widgetsBar, maxval=pDocCsvNumpy.shape[0]).start()


        #Read CSV-file cell by cell and save it to numpy array
        #-------------------------------------------------------------------------------
        #Rows represent time, columns data
        cnRow = 0 #Counter rows, index is cnRow-1
        for row in pDocCsv: #Each row in file
            cnCol = 0 #Counter columns, index is cnCol-1
            cnRow = cnRow + 1
            #print cnRow

            for col in row: #Each cell in row
                cnCol = cnCol + 1
                #print cnCol

                try: #Only read float values = data values 
                    input = numpy.cast[pDataType](col) #input = e.g. float(col)
                    pDocCsvNumpy[cnRow-1, cnCol-1] = input   #save each cell value to numpy array

                    #print 'Value at row:', cnRow, '; column: ', cnCol, '; value: ' \
                    #, pDocCsvNumpy[cnRow-1, cnCol-1] #Index values beginning with '0', not number of cols, rows

                except: #Values that are not numbers, like alphabetic values or ''
                    input = numpy.cast[pDataType](nodata_) #input = e.g. float(nodata_)
                    pDocCsvNumpy[cnRow-1, cnCol-1] = input   #Save default no-data value to cell

                    self.pLogger.warning("Value '" + str(col) + "' at row '" + str(cnRow) + "' and column '" + str(cnCol) + \
                    "' is not of data type '" + str(pDataType) + "'. Use nodata value '" + str(pDocCsvNumpy[cnRow-1, cnCol-1]) + "' instead.")
                    #Index values beginning with '0', not number of cols, rows

                    if isVarName_:
                        if cnRow == 1: #If first row has no numbers, it is assumed that these are the column names
                            if col != '':
                                self.pVarNames.append(col) 
                            else: #If col = '' write col number
                                self.pVarNames.append('variable #'+str(cnCol-1)) #zero based
                            #print 'Variable names yet detected at first row:', self.pVarNames

                progressBar.update(cnRow)# Progress bar

        if isVarName_:   #If first row has var_names, delete first row that consists of nodata_values in numpy array
            pDocCsvNumpy = numpy.delete(pDocCsvNumpy, 0, 0 )
            self.pLogger.info("Detected variable names in first row of file: '" + str(self.pVarNames) + "'")

        return pDocCsvNumpy


    def choseSpecificData(self, pCsvData_, nodata_, isVarName_):
        """Optional: Extract those information that is wanted and save it in new numpy array"""

        self.pLogger.info("Extract specific data as implemented in function 'choseSpecificData'...")

        pCsvData = pCsvData_

        nCols = pCsvData.shape[1] #Value axes
        nRows = pCsvData.shape[0] #Time axes
       
        #Extract specific data
        #-------------------------------------------------------------------------------
        dimTime = nRows
        dimVar = 4  #Number of variables in file

        #Output file dimension order: time, variable
        pNumpyData = numpy.zeros((dimTime, dimVar), dtype = pCsvData.dtype)

        #Copy specific information to new output file
        for i_time in range(0,dimTime,1):
            pNumpyData[i_time, 0] = pCsvData[i_time, 3]    #Global
            pNumpyData[i_time, 1] = pCsvData[i_time, 6]    #Reflected
            pNumpyData[i_time, 2] = pCsvData[i_time, 9]    #Atmo
            pNumpyData[i_time, 3] = pCsvData[i_time, 10]   #Surface
            
        if isVarName_:   #if first row has var_names
            self.pVarNames[0] =  self.pVarNames[3]
            self.pVarNames[1] =  self.pVarNames[6]
            self.pVarNames[2] =  self.pVarNames[9]
            self.pVarNames[3] =  self.pVarNames[10]

        return pNumpyData


    def writeNumpyData(self, pNumpyData_):
        """Export numpy data array to file"""

        self.pLogger.info("Numpy output will be file saved as '"+ str(self.numpyDataName) + "'...")
        numpy.save(str(self.numpyDataName), pNumpyData_) #Better as 'tofile'. Also possible: 'dump'
        self.pLogger.info("Done. Shape of resulting numpy file: '" + str(pNumpyData_.shape) + "'; Data type: '" + str(pNumpyData_.dtype) + "'.")

        return


    def writeMetadataNcml(self, nodata_, isVarName_):
        """Create new NCML XML file according to the specifications of the data model and
        complete this file by the metadata that can be extracted out of the CSV file"""

        #Get metadata information from file
        #-------------------------------------------------------------------------------
        pNumpyData = numpy.load(self.numpyDataName)
        dimVar = pNumpyData.shape[1]
        
        #Define progress bar settings
        widgetsBar = ['Creating Ncml metadata file: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
        progressBar = ProgressBar(widgets=widgetsBar, maxval=dimVar).start()

        #Write metadata NCML file
        #-------------------------------------------------------------------------------
        self.pProcessNcml.createMacroNcmlFile() #Create NCML macro file for gridded data
        self.pProcessNcml.fillNcmlMacroWithNumpy(pNumpyData) #only for grids
        self.pProcessNcml.changeMacroForStation() #Change macro for station data

        #Correct and complete entries
        for i_var in range(0,dimVar,1): # otherwise returns list of ints from >= start and < end: 0 .. 10
            varName = 'variable #'+str(i_var)
            if isVarName_: #Use variable names of list in case that first row of CSV file contained variable names
                varNameNew = self.pVarNames[i_var]
            else: #otherwise use generic variable names 'varName'
                varNameNew = varName

            self.pProcessNcml.changeVariable(varName, 'name', varNameNew)
            self.pProcessNcml.changeLocalAttribute(varNameNew, '_FillValue', 'value', str(nodata_))
            stringVarCoordinates = str(self.pDefaultSettings.axisTimeName) + " " + str(self.pDefaultSettings.axisHeightName) \
                + " " + str(self.pDefaultSettings.axisLatitudeName) + " " + str(self.pDefaultSettings.axisLongitudeName)
            self.pProcessNcml.addLocalAttribute(varNameNew, "coordinates", stringVarCoordinates, "", "")# necessary for station data!

            progressBar.update(i_var+1)# Progress bar

        return


    def writeMetadataNumpymeta(self):
        """Create new metadata coordinate XML file according to the specifications of the data model and
        complete this file by the metadata that can be extracted out of the CSV file"""

        self.pProcessNumpymeta.createMacroNumpymetaFile()
        return


    #Other functions
    #-------------------------------------------------------------------------------

    def __openCsvFile(self):
        """Read CSV file"""

        if not self.csvFileName.endswith('.csv'): #Add filename suffix '.csv' if this is missing
            self.csvFileName = self.csvFileName + '.csv'

        #csv.reader(csvfile[, dialect='excel'][, fmtparam])
        try:
            pDocCsv = csv.reader(open(self.csvFileName, 'r') , dialect= CSV_DIALECT)
        except:
            raise Exception ("Opening of file '" + str(self.csvFileName) + "' failed. Check if it exists and if filename suffix is set.")
       
        return pDocCsv


    #Data specific functions
    #-------------------------------------------------------------------------------

    def completeDataVariables(self):
        """Complete missing data variable value modification manually

        Example: Scale data values in case that units prefix have to be changed
        (e.g. from hPa to Pa) due to defined unit in standard_name entry."""

        #pCsvData = numpy.load(self.numpyDataName)
        #--> Nothing to do at the moment
        #numpy.save(self.numpyDataName, pCsvData) #Better then 'tofile'. Also possible: 'dump'

        return


    def completeMetadataNcml(self):
        "Complete missing data in NCML XML file manually"

        self.pProcessNcml.changeGlobalAttribute('title', 'value', 'CR10_Lhasa_All2010')
        self.pProcessNcml.changeGlobalAttribute('source', 'value', 'No information available')
        self.pProcessNcml.changeGlobalAttribute('references', 'value', 'No information available')
        self.pProcessNcml.changeGlobalAttribute('comment', 'value', 'Kipp & Zonen CM14 pyranometer; 2x Kipp & Zonen CGR4 pyrgeometer')

        self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'units', 'value', 'm') #'Level' is not conform to udunits!
        self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'long_name', 'value', 'altitude')
        self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'standard_name', 'value', 'altitude')

        self.pProcessNcml.changeLocalAttribute('Global', 'units', 'value', 'W m-2')
        self.pProcessNcml.changeLocalAttribute('Global', 'long_name', 'value', 'global data from albedo')
        self.pProcessNcml.changeLocalAttribute('Global', 'standard_name', 'value', 'toa_net_downward_radiative_flux')

        self.pProcessNcml.changeLocalAttribute('Reflected', 'units', 'value', 'W m-2')
        self.pProcessNcml.changeLocalAttribute('Reflected', 'long_name', 'value', 'reflected data for albedo')
        self.pProcessNcml.changeLocalAttribute('Reflected', 'standard_name', 'value', 'toa_cloud_radiative_effect')

        self.pProcessNcml.changeLocalAttribute('Atmo', 'units', 'value', 'W m-2')
        self.pProcessNcml.changeLocalAttribute('Atmo', 'long_name', 'value', 'radiation measurement direction atmosphere')
        self.pProcessNcml.changeLocalAttribute('Atmo', 'standard_name', 'value', 'surface_net_downward_radiative_flux')

        self.pProcessNcml.changeLocalAttribute('Surface', 'units', 'value', 'W m-2')
        self.pProcessNcml.changeLocalAttribute('Surface', 'long_name', 'value', 'radiation measurement direction surface')
        self.pProcessNcml.changeLocalAttribute('Surface', 'standard_name', 'value', 'surface_net_upward_radiative_flux')

        return


    def completeMetadataNumpymeta(self):
        "Complete missing data in metadata coordinate XML file manually"

        pNumpyData = numpy.load(self.numpyDataName)

        #Reference time of data in NetCDF metadata format, calculate time values
        pTimes = self.pProcessingTool.createTimeValuesNumpy('hours since 2010-04-03 06:00:0.0', pNumpyData.shape[0], 0.5)
        self.pProcessNumpymeta.writeNumpyMetadataValues(pTimes, 'time')  #Either time values or min/max

        self.pProcessNumpymeta.setAttribute('numpymeta', 'longitude', 'values', '91.031778')
        self.pProcessNumpymeta.setAttribute('numpymeta', 'latitude', 'values', '29.644694')
        self.pProcessNumpymeta.setAttribute('numpymeta', 'height', 'values', '3636')
        self.pProcessNumpymeta.setAttribute('numpymeta', 'id', 'values', '1')

        return


#_______________________________________________________________________________

def main():
    """
    Main function.

    This function represents the user interface and is called when the
    program is executed. Start the program by executing it with the following
    statement in your shell to get more information: csv_2Interface.py --help
    """

    startTime = time.time()
    pDefaultSettings = DefaultSettings()

    #Parser definition
    #-------------------------------------------------------------------------------
    pParser = OptionParser(usage=USAGE, version = VERSION, description = DESCRIPTION, epilog = EPILOG)

    pParser.set_defaults(completeModel = False)
    pParser.set_defaults(isDoc = False)
    pParser.set_defaults(logLevel = pDefaultSettings.loggerLevelConsole)
    pParser.set_defaults(nodataValue = NODATA)
    pParser.set_defaults(dataPath = pDefaultSettings.dataDirectory) 
    pParser.set_defaults(isSpecificData = False)
    pParser.set_defaults(dataType = NUMPYDATA_DTYPE)
    pParser.set_defaults(isVarName = False) #First row of CSV file contains variable name information


    pParser.add_option("-c", "--complModel", action="store_true",  dest='completeModel', help="Complete data model by functions particularly written for specific data (default = %default)")
    pParser.add_option("-d", "--doc", action="store_true",  dest='isDoc', help="Give more information by printing docstrings (default = %default)")
    pParser.add_option('-l', '--log', action = 'store', dest='logLevel', choices = ['debug','info','warning','error','critical'], nargs = 1, help="Minimum level for printing information to the console (default = %default)")
    pParser.add_option('-n', '--nodata', action = 'store', dest='nodataValue', nargs = 1, help="Set nodata value (default = %default)")
    pParser.add_option('-p', '--path', action = 'store', type ='string', dest='dataPath', nargs = 1, help="Directory for input / output files (default = %default)")
    pParser.add_option('-s', '--specData', action='store_true',  dest='isSpecificData', help="Only extract specific data as implemented in function 'choseSpecificData' (default = %default)")
    pParser.add_option('-t', '--dtype', action = 'store', dest='dataType', choices = [''] + NUMPY_DTYPES, nargs = 1, help="Define output data type of numpy array (default = %default)")
    pParser.add_option('-v', '--varNames', action='store_true',  dest='isVarName', help='First row in CSV file contains variable names (default = %default)')

    (options, args) = pParser.parse_args()


    #Initialize logger
    #-------------------------------------------------------------------------------
    pLog = LoggingInterface(MODULE_LOGGER_ROOT, options.logLevel, pDefaultSettings.loggerLevelFile) #Instance is necessary although if not used.
    pLogger = logging.getLogger(MODULE_LOGGER_ROOT+"."+__name__)
    pLogger.info("_____________________________________________________________________________________________")
    pLogger.info("Starting program 'CSV2INTERFACE' version '" + str(__version__) + "' from '" + str(__date__) + "':")


    try:

        #Parse command line arguments and options
        #-------------------------------------------------------------------------------
        if len(args) != 2:
            pLogger.error("Parser error occured. See error messages on the screen.")
            pParser.error("Incorrect number of arguments. Two arguments 'operation' and 'data' are nedded. " \
            +str(len(args))+" arguments are given. Execute '%prog --help' for more information")
        else:
            #args = sys.argv[1:]#sys.argv[0] is name of program being executed
            operation_ = args[0]
            infile_ = args[1]


        #Process parser options
        #-------------------------------------------------------------------------------
        if options.isDoc:
            pLogger.info(__doc__)
            sys.exit(0)

        dataPath = options.dataPath
        if not dataPath.endswith('/') and dataPath != '': #Adds '/' to path in case that this is not the case
            dataPath = dataPath+'/'
        infileName = dataPath+infile_ #Add path of data directory to filename


        #Run program
        #-------------------------------------------------------------------------------
        pControlModelCsv = ControlModelCsv(infileName, options)

        if operation_ == 'csv2Model':
            pLogger.info("Operation: Convert CSV to data model")
            pControlModelCsv.writeCsvNumpyData() #Write numpy data array
            pControlModelCsv.writeCsvMetadata() #Write metadata

            if options.completeModel:#optional
                pControlModelCsv.completeDataModelManually() #Complete data model manually

        else:
            pLogger.error("Parser error: Operation '" + str(operation_) + "' is unknown.")
            pParser.error("Operation '" + str(operation_) + "' is unknown.") #System exit code 2


    except Exception: #If Exceptiation occured in this module or all connected sub-modules
        pLogger.exception('Exception Error occured: ')
        raise

    finally:
        pLogger.info("Finished. Total processing time [s]: '" + str(time.time() - startTime) + "'.")
        pLogger.info("_____________________________________________________________________________________________")
        pLog.__del__()

        #pControlModelCsv.__del__()


if __name__ == "__main__":
      main()
