#! /usr/bin/python
# -*- coding: latin1 -*-

"""
Converts a GRADS readable dataset to the data model.

Module for reading a GRADS compatible raster file and exporting it to the data model
(or netCDF-file by using GRADS functions) that is  consisting of the following files:
files numpy data array,coordinate metadata xml file and NCML NetCDF XML file.
Data is considered as grid, therefore the shape of the output numpy array is:
(variable, time, z, lat, lon). This program was particularly written to convert
GRAPES GRIB raster files. Find more information in the documentation.
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-03-28"
__version__ = "v0.1.3" #MajorVersion(backward_incompatible).MinorVersion(backward_compatible).Patch(Bug_fixes)


#Changelog
#-------------------------------------------------------------------------------
#2011-01-14: v0.1.3 logging implemented, functionalities changed
#2010-12-14: v0.1.2 parser added, functionalities changed
#2010-11-24: v0.1.1 comments and docstrings added
#2010-11-15: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
import sys
import time
from optparse import OptionParser #Parser
import logging

#related libraries
import numpy

#Importing GRADS
#Extends the GrADS client class GaCore, providing methods for exchanging
#n-dimensional NumPy array data between Python and GrADS.
import grads.ganum as ganum

#This module extends the GrADS client class by providing methods for
#exchanging n-dimensional NumPy array data between Python and GrADS
#import grads.numtypes as numtypes

#A simple container class to collect output for query() operations.
#import grads.gahandle as gahandle


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
    \n    - grads2Model     Convert GRADS raster image file (here GRAPES GRIB data) to data model\
    \n    - printGrads      Read GRADS file and print it on screen\
    \n    - testGrads       Test GRADS functionalities\
    \n\
    \ndata:\
    \n    Raster data file that is readable by GRADS library"

DESCRIPTION= "Conversion tool of CEOP-AEGIS data model for GRADS readable raster data"
EPILOG = "Author: "+__author__+" (E-mail: "+__author_email__+")"

VERSION = "%prog version "+__version__+" from "+__date__


#Module default values / constants, may be overwritten by OptionParser
#-------------------------------------------------------------------------------
NUMPYDATA_DTYPE = 'float32' #Default data type of output numpy array
NODATA = 0 #Default nodata value of output numpy array

#Multiplicator for each time value, should be same unit as of reference time
#Value can't yet be extracted of Grib Metadata automatically. See Grib Metadata file for finding this value
DATATIMESTEP = 0.5 

MODULE_LOGGER_ROOT = 'grads' #Logger root name

#_______________________________________________________________________________

class ControlModelGrads:
    """Control class for model 'ModelGradsRead'. This class is providing all available functions for reading data"""

    def __init__(self, infile_, option_):
        """
        Constructor for new control instance of specific file.

        INPUT_PARAMETERS:
        infile      - name of data file with filename extension (string)
        option      - Parser.options arguments

        COMMENTS:
        Suffixes will be automatically assigned and must respect the declarations
        in the module 'interface_Settings'.
        """
       
        infile = str(infile_).rsplit('__',1)
        self.inputFile = infile[0]
        self.pModelGradsRead = ModelGradsRead(self.inputFile)

        self.pParserOptions = option_
        self.pLogger = logging.getLogger(MODULE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)
        self.pLogger.info("Open project '" + self.inputFile + "':")
       

    #def __del__(self):
        #"""Desctructor"""
        

    def writeGradsNumpyData(self):
        """Read GRADS file and save data as numpy data array according to the specifications
        of the data interface"""

        #Make a copy of the GRADS-file as numpy file
        pGradsData = self.pModelGradsRead.readGradsFile(self.pParserOptions.dataType)
              
        #Optional to select specific data from time stamp
        if not self.pParserOptions.specificData is None: #specificData is choosen
            pGradsData = self.pModelGradsRead.choseSpecificData(pGradsData, self.pParserOptions.specificData)

        #Export data as new numpy file
        self.pModelGradsRead.writeNumpyData(pGradsData)
        return


    def writeGradsMetadata(self):
        """Get metadata from a GRADS readable file and write metadata to coordinate metadata file and
        NCML XML file according to the specifications of the data interface"""

        self.pModelGradsRead.writeMetadataNcml(self.pParserOptions.nodataValue)
        self.pModelGradsRead.writeMetadataNumpymeta(self.pParserOptions.specificData)
        return


    #optional
    def completeDataModelManually(self):
        """Complete missing data and metadata manually"""

        self.pModelGradsRead.completeDataVariables()
        self.pModelGradsRead.completeMetadataNcml()
        self.pModelGradsRead.completeMetadataNumpymeta() #not implemented
        return


    #optional
    def printGradsMetadata(self):
        """Read GRADS readable file and print metadata on screen"""

        self.pModelGradsRead.printGradsMetadata()
        return


    #optional
    def testGradsFunctionality(self):
        """Test GRADS functionality by testing its functions and creating a NetCDF
        file automatically"""

        self.pModelGradsRead.grib2NetCdf_gradsTest()
        return


#_______________________________________________________________________________

class ModelGradsRead:
    """This class contains functions to handle read operations on GRADS data and is controlled by
    the class 'ControlModelGrads'.
    This class was in particularly written to handle GRAPES GRIB data."""


    def __init__(self, infile_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - name of GRADS file name with filename extension (string)
        """
        self.pDefaultSettings = DefaultSettings()
        
        self.gradsFileName = infile_ #With file name extension

        #infile = self.gradsFileName.rsplit('.',1) #without file name extension
        self.numpyDataName = infile_+FILENAME_SUFFIX_NUMPYDATA
        self.ncmlName = infile_+FILENAME_SUFFIX_NCML
        self.numpymetaName = infile_+FILENAME_SUFFIX_NUMPYXML

        #Use Processing Tools
        self.pProcessingTool = ProcessingTool()
        self.pProcessNcml = ProcessNcml(self.ncmlName)
        self.pProcessNumpymeta = ProcessNumpymeta(self.numpymetaName)

        self.pLogger = logging.getLogger(MODULE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)

        #Read GRADS file
        #Start the GRADS application, creating new instance
        #Depending on GRADS version, 'Bin' is telling which GRADS executable to start
        #For 2.0a7 this is 'grads' and 'gradsdap'
        try:
            self.pGa = ganum.GaNum(Bin='grads', Echo=False, Window=False)
            self.pGa.open(self.gradsFileName)
        except:
            raise Exception ("Opening of file '" + str(self.gradsFileName) + "' failed. Check if it exists and if filename suffix is set.")
            

    def __del__(self):
        """Destructor"""
        #Close GRADS instance
        del self.pGa


    def readGradsFile(self, dataType_):
        """Reads a GRADS file and returns GRADS data as numpy array.
        Argument 'dataType' defines the data type of the resulting numpy array."""

        pGa = self.pGa
     
        #Get file information via GRADS
        #-------------------------------------------------------------------------------
        # Query dataset information, command available for "file" and "dims"
        pGa_queryFile = pGa.query("file")
        pGa_queryDims = pGa.query("dims")

        #Get dimension values and set dimensions
        dimX = pGa_queryFile.nx   #number of longitude points
        dimY = pGa_queryFile.ny   #number of latitude points
        #dimZ = pGa_queryFile.nz   #z-dimension not used in GRAPES data, level = 1
        dimT = pGa_queryFile.nt   #number of time values in file
        dimVar = pGa_queryFile.nvars  #numbers of variables in file

        varsNames = pGa_queryFile.vars     #names of variables in file

        pGa("set z 1") #GRADS command to set dimensions
        pGa("set t 1 last") #Get all time values; define timestamp later in python

        #Define progress bar settings
        widgetsBar = ['Import status: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
        progressBar = ProgressBar(widgets=widgetsBar, maxval=dimVar).start()

        #Print Dataset information on the screen
        #print "\nCoordinate information: \n", pGa.coords()
        #print "\nFile information: \n", pGa_queryFile
        #print "\nDimension information: \n", pGa_queryDims


        #Writing numpy file
        #-------------------------------------------------------------------------------
        pDataType = self.pProcessingTool.dataType_2Numpy(dataType_)
        pGradsData = numpy.zeros((dimVar,dimT,dimY,dimX), dtype = pDataType)# All data
        
        #Reading all variables in GRADS file
        for i_var in range(0,dimVar,1): # otherwise returns list of ints from >= start and < end: 0 .. 10

            self.pLogger.info("Reading GRADS variable ID '" + str(i_var) + "' with name '" + str(varsNames[i_var]) + "'...")
            pDataArray = pGa.expr(varsNames[i_var]) #Export GRADS field of specific variable as numpy-like array
          
            #Create a numpy file per file, so for all variables per file
            pGradsData[i_var,:,:,:] = numpy.asarray(pDataArray.astype(pDataType))

            progressBar.update(i_var+1)# Progress bar


        #Change dimensions of numpy array so that it gets conform with the data model specifications
        #-------------------------------------------------------------------------------
        dimVar = pGradsData.shape[0] #Number of variables in array
        dimT = pGradsData.shape[1] #Time Dimension
        dimZ = int(1) #Level Dimensions
        dimY = pGradsData.shape[2] #Last but one axis top to bottom: lat -> row
        dimX = pGradsData.shape[3] #Last axis left to right: lon -> col

        pBuffer = numpy.zeros((dimY,dimX), dtype = pGradsData.dtype) #Buffer for calculation
        pGradsDataNorm = numpy.zeros((dimVar,dimT,dimZ,dimY, dimX), dtype = pGradsData.dtype) #Normed numpy data array

        #Change dimension order that is "var,time,y,x' and is to be 'var,time,level,y,x'.
        #This is neccessary so that the time variables dimension can be set to unlimited (only possible for first variable).
        #Define progress bar settings
        widgetsBar = ['Making data conform for data model: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
        progressBar = ProgressBar(widgets=widgetsBar, maxval=dimVar).start()

        for i_var in range(0,dimVar,1):
            for i_time in range(0, dimT, 1):
                pBuffer[:,:] = pGradsData[i_var,i_time,:,:] #Extract data to buffer
                pGradsDataNorm[i_var,i_time,0,:,:] = pBuffer[:,:]  #Write Data in output numpy array

            progressBar.update(i_var+1)# Progress bar

        return pGradsDataNorm


    def choseSpecificData(self, pGradsData_, dataTime_):
        """Optional: Extract those datasets that fall within the wanted timestamp

        Define time stamp in list dataTime. dataTime[0] is start value, dataTime[1]
        end value, as time units since reference time.        
        Example: nt = 97 values; first (1st) value first day 0h00, half hour steps,
        96th value: second day 23h30, 97th value third day 0h00
        Time intervall has for example to consist of 24 hours, so 47 values!
        position numbers (start value = 1, not 0!!!), not index numbers of arrays; needed for dimension setting
        DATASTART = 25 #12h00 first day
        DATASTOP = 72  #11h30 second day
        """

        self.pLogger.info("Extract specific data as implemented in function 'choseSpecificData'...")

        pGradsData = pGradsData_
        dataStart = int(dataTime_[0])
        dataStop = int(dataTime_[1])

        #Define progress bar settings
        widgetsBar = ['Extracting specific data: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
        progressBar = ProgressBar(widgets=widgetsBar, maxval=(dataStop-(dataStart-1))).start()


        #Get all datasets from wanted time intervall. Index of time value is defined in
        #global variables. Export data as numpy file

        #Number of time values for wanted time stamp
        grapesTimeStamp = dataStop - dataStart + 1#dimension value, not index value for array!!! E.g. (48-1)+1=48

        #Only GRADS data of wanted time stamp
        pGradsDataTS = numpy.zeros((pGradsData.shape[0],grapesTimeStamp,pGradsData.shape[2],\
            pGradsData.shape[3], pGradsData.shape[4]), dtype = pGradsData.dtype)

        #!Range: Last value not taken for iteration! So don't use DATASTOP-1, but DATASTOP!
        i = 0
        for j in range(dataStart-1, dataStop, 1): #array index numbers, not position numbers
            pGradsDataTS[:,i,:,:,:] = pGradsData[:,j,:,:,:]
            i = i+1

            progressBar.update(j-(dataStart-1)+1)# Progress bar
        
        return pGradsDataTS


    def writeNumpyData(self, pNumpyData_):
        """Export numpy data array to file"""

        self.pLogger.info("Numpy output will be file saved as '"+ str(self.numpyDataName) + "'...")
        numpy.save(str(self.numpyDataName), pNumpyData_) #Better as 'tofile'. Also possible: 'dump'
        self.pLogger.info("Done. Shape of resulting numpy file: '" + str(pNumpyData_.shape) + "'; Data type: '" + str(pNumpyData_.dtype) + "'.")

        return


    def writeMetadataNcml(self, nodata_):
        """Create new NCML XML file according to the specifications of the data model and
        complete this file by the metadata that can be extracted out of the GRADS file"""

        #Get metadata information from file 
        #-------------------------------------------------------------------------------
        pGa = self.pGa
        pGa_queryFile = pGa.query("file") # Query dataset information, command available for "file" and "dims"

        pNumpyData = numpy.load(self.numpyDataName)

        dimVar = pNumpyData.shape[0] #Number of variables in array
        varsNames = pGa_queryFile.vars #names of variables on file
        varsTitles = pGa_queryFile.var_titles #var_titles are equivalent to long_name

        #Define progress bar settings
        widgetsBar = ['Creating Ncml metadata file: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
        progressBar = ProgressBar(widgets=widgetsBar, maxval=dimVar).start()
       
        #Write metadata NCML file
        #-------------------------------------------------------------------------------
        self.pProcessNcml.createMacroNcmlFile()
        self.pProcessNcml.fillNcmlMacroWithNumpy(pNumpyData) 

        #Correct and complete entries
        self.pProcessNcml.changeGlobalAttribute('title', 'value', pGa_queryFile.title)

        for i_var in range(0,dimVar,1): # otherwise returns list of ints from >= start and < end: 0 .. 10
            varName = 'variable #'+str(i_var)
            varsDescriptions = varsTitles[i_var].rsplit('0  ') #To get rid of weird values at beginning
            
            self.pProcessNcml.changeVariable(varName, 'name', varsNames[i_var])
            self.pProcessNcml.changeLocalAttribute(varsNames[i_var], 'long_name', 'value', varsDescriptions[1])
            self.pProcessNcml.changeLocalAttribute(varsNames[i_var], '_FillValue', 'value', str(nodata_))

            progressBar.update(i_var+1)# Progress bar

        return


    def writeMetadataNumpymeta(self, dataTime_):
        """Create new metadata coordinate XML file according to the specifications of the data model and
        complete this file by the metadata that can be extracted out of the GRADS file"""

        pGa = self.pGa

        #Get metadata information from file by the use of GRADS
        #-------------------------------------------------------------------------------
        #Query dataset information, command available for "file" and "dims"
        pGa_queryDims = pGa.query("dims")
        pGa_queryFile = pGa.query("file")

        #Get latitude / longitude values
        latMin = pGa_queryDims.lat[0]#ymin
        latMax = pGa_queryDims.lat[1]#ymax
        lonMin = pGa_queryDims.lon[0]#xmin
        lonMax = pGa_queryDims.lon[1]#xmax

        #Get time values
        #Number of time values for wanted time stamp, otherwise DimT
        if not dataTime_ is None: #specificData is choosen
            dataStart = int(dataTime_[0])
            dataStop = int(dataTime_[1])
        else:
            dataStart = 1
            dataStop = pGa_queryFile.nt #dimT, number of time values in file
        grapesTimeStamp = dataStop - dataStart + 1 #Dimension value, not index value for array!!! E.g. (48-1)+1=48

        referenceTimeGrib = pGa_queryDims.time[0] #Reference time of data in grib metadata format
        referenceTimeNetCdf = self.__timeUnitGrib2NetCdf(referenceTimeGrib, dataStart) #Reference time of data translated to NetCDF metadata format
        pTimes = self.pProcessingTool.createTimeValuesNumpy(referenceTimeNetCdf, grapesTimeStamp, DATATIMESTEP) #Calculate time values


        #Write coordinate metadata file
        #-------------------------------------------------------------------------------
        self.pProcessNumpymeta.createMacroNumpymetaFile()

        self.pProcessNumpymeta.writeNumpyMetadataValues(pTimes, 'time') #Either time values or min/max

        self.pProcessNumpymeta.setAttribute('numpymeta', 'latitude', 'min', str(latMin))
        self.pProcessNumpymeta.setAttribute('numpymeta', 'latitude', 'max', str(latMax))
        self.pProcessNumpymeta.setAttribute('numpymeta', 'longitude', 'min', str(lonMin))
        self.pProcessNumpymeta.setAttribute('numpymeta', 'longitude', 'max', str(lonMax))

        self.pProcessNumpymeta.setAttribute('numpymeta', 'height', 'values', str(1))
        self.pProcessNumpymeta.setAttribute('numpymeta', 'height', 'separator', str(','))

        return


    #Other functions
    #-------------------------------------------------------------------------------

    def printGradsMetadata(self):
        """Read GRADS file and print metadata on screen"""

        infile = self.gradsFileName

        ga = ganum.GaNum(Bin='grads', Echo=False, Window=True)#Starts the GRADS application
        #Depending on GRADS version, bin is telling which GRADS executable to start
        #For 2.0a7 this is 'grads' and 'gradsdap'
        try:
            fh = ga.open(infile)
        except:
            raise Exception("Error: GRADS file does not exist: '" + str(infile) + "'.")
            exit()

        #Query metadata information
        qh_file = ga.query("file")
        qh_dims = ga.query("dims")

        #Print metadata information on screen
        self.pLogger.info("---------------------------------------------------------------------")
        self.pLogger.info("File information:")
        self.pLogger.info(qh_file)
        self.pLogger.info("Dimension information:")
        self.pLogger.info(qh_dims)
        self.pLogger.info("---------------------------------------------------------------------")

        return


    def __timeUnitGrib2NetCdf(self, timeGribStart_, dataStart_):
        """Transforms reference time from Grib metadata format to time format of
        NetCDF time units attribute. timeGribStart is reference time, dataStart
        is offset time."""

        #Get time values from infofile and adapt data
        #-------------------------------------------------------------------------------
        fileTimeStart = timeGribStart_ #Start value of data

        if len(fileTimeStart) == 12: #Data format for example 00Z11JAN2008
            timestart_time = fileTimeStart[0:2]+':00:0.0'
            timestart_day = fileTimeStart[3:5]
            timestart_month = fileTimeStart[5:8]
            timestart_year = fileTimeStart[8:12]
            #print timestart_year, timestart_month, timestart_day, timestart_time
        elif len(fileTimeStart) == 15: #Data format for example 00:30Z11JAN2008
            timestart_time = fileTimeStart[0:5]+':0.0'
            timestart_day = fileTimeStart[6:8]
            timestart_month = fileTimeStart[8:11]
            timestart_year = fileTimeStart[11:15]
            #print timestart_year, timestart_month, timestart_day, timestart_time
        else:
             raise Exception("Error in function 'timeUnitGrib2NetCdf': Time specification in infofile can't be read, process aborted...")
             
        #Change month from word statement to number
        if timestart_month == 'JAN':
            timestart_month_nr = '01'
        elif timestart_month == 'FEB':
            timestart_month_nr = '02'
        elif timestart_month == 'MAR':
            timestart_month_nr = '03'
        elif timestart_month == 'APR':
            timestart_month_nr = '04'
        elif timestart_month == 'MAI':
            timestart_month_nr = '05'
        elif timestart_month == 'JUN':
            timestart_month_nr = '06'
        elif timestart_month == 'JUL':
            timestart_month_nr = '07'
        elif timestart_month == 'AUG':
            timestart_month_nr = '08'
        elif timestart_month == 'SEP':
            timestart_month_nr = '09'
        elif timestart_month == 'OCT':
            timestart_month_nr = '10'
        elif timestart_month == 'NOV':
            timestart_month_nr = '11'
        elif timestart_month == 'DEC':
            timestart_month_nr = '12'
        else:
            raise Exception("Error in function 'timeUnitGrib2NetCdf': Month specification in infofile corrupt, process aborted...")
            
########### Hack to change timeUnitNetCdf in case that not all GRAPES data is used (like here the timestamp)
        offsetTime = (dataStart_ - 1) * DATATIMESTEP #(25-1)*0.5=12h00
        if (offsetTime < 24 and offsetTime % 2 == 0): #must be full hours
            timestart_time_hours = int(timestart_time[0:1])+int(offsetTime)
            timestart_time = str(timestart_time_hours)+str(timestart_time[2:9])
        else:
            raise Exception ("Error in function 'timeUnitGrib2NetCdf': time offset >= 24 is not implemented yet! DATATIMESTEP unless full hours is not implemented yet!")


        #Set NetCDF time unit, e.g. "hours since 2008-01-11 00:00:0.0"
        #-------------------------------------------------------------------------------
        timeUnitNetCdf = 'hours since '+ str(timestart_year)+ '-'+ str(timestart_month_nr)+\
        '-'+ str(timestart_day)+' '+ str(timestart_time)

        return timeUnitNetCdf


    def grib2NetCdf_gradsTest(self):
        """Test GRADS functionality by testing functions and creating a NetCdf file"""

        #Open file
        infile = self.gradsFileName

        ga = ganum.GaNum(Bin='grads', Echo=False, Window=True)#Starts the grads application
        #Depending on Grads version, bin is telling which grads executable to start
        #For 2.0a7 this is 'grads' and 'gradsdap'
        try:
            fh = ga.open(infile)
        except:
            raise Exception("Error: GRADS file does not exist: '" + str(infile) + "'.")
            exit()

        #Printing metadata on screen
        qh_file = ga.query("file")
        qh_dims = ga.query("dims")

        self.pLogger.info("---------------------------------------------------------------------")
        self.pLogger.info("File information:")
        self.pLogger.info(qh_file)
        self.pLogger.info("Dimension information:")
        self.pLogger.info(qh_dims)
        self.pLogger.info("---------------------------------------------------------------------")


        #Create one netCDF-file of specific variable by using GRADS commands
        ga("set z 1")
        ga("set t 1 last")

        ga("display gsw")
        ga("define out = gsw")
        ga("set sdfwrite output_file_GRADS_gsw.nc")
        ga("sdfwrite out")

        raw_input("Press Enter to terminate.") #Wait

        del ga

        return


    #Data specific functions
    #-------------------------------------------------------------------------------

    def completeDataVariables(self):
        """Complete missing data variable value modification manually

        Example: Scale data values in case that units prefix have to be changed
        (e.g. from hPa to Pa) due to defined unit in standard_name entry."""

        pGradsData = numpy.load(self.numpyDataName)

        #Scale of data. Here: data is in hPa, must be in Pa
        pGradsData = self.pProcessingTool.scaleNumpyDataVariable(pGradsData, 5, 100.0) #p_pbl
        pGradsData = self.pProcessingTool.scaleNumpyDataVariable(pGradsData, 7, 100.0) #ps
        pGradsData = self.pProcessingTool.scaleNumpyDataVariable(pGradsData, 8, 100.0) #psl

        numpy.save(self.numpyDataName, pGradsData) #Better then 'tofile'. Also possible: 'dump'

        return


    def completeMetadataNcml(self):
        "Complete missing data in NCML XML file manually"

        self.pProcessNcml.changeGlobalAttribute('source', 'value', 'No information available')
        self.pProcessNcml.changeGlobalAttribute('references', 'value', 'No information available')
        self.pProcessNcml.changeGlobalAttribute('comment', 'value', 'No information available')

        self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'units', 'value', '1') #'Level' is not conform to udunits!
        self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'long_name', 'value', 'level')
###############Define Standard Name!
        #self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'standard_name', 'value', '???')
        self.pProcessNcml.removeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'standard_name')

        self.pProcessNcml.changeLocalAttribute('pblh', 'units', 'value', 'm')
        self.pProcessNcml.changeLocalAttribute('pblh', 'standard_name', 'value', 'atmosphere_boundary_layer_thickness')
    
        self.pProcessNcml.changeLocalAttribute('tpbl', 'units', 'value', 'K')
        self.pProcessNcml.changeLocalAttribute('tpbl', 'standard_name', 'value', 'tropopause_air_temperature')
    
        self.pProcessNcml.changeLocalAttribute('qpbl', 'units', 'value', 'kg kg-1')
        self.pProcessNcml.changeLocalAttribute('qpbl', 'standard_name', 'value', 'specific_humidity')
    
        self.pProcessNcml.changeLocalAttribute('upbl', 'units', 'value', 'm s-1')
        self.pProcessNcml.changeLocalAttribute('upbl', 'standard_name', 'value', 'x_wind')
    
        self.pProcessNcml.changeLocalAttribute('vpbl', 'units', 'value', 'm s-1')
        self.pProcessNcml.changeLocalAttribute('vpbl', 'standard_name', 'value', 'y_wind')
    
        self.pProcessNcml.changeLocalAttribute('p_pbl', 'units', 'value', 'Pa')
        self.pProcessNcml.changeLocalAttribute('p_pbl', 'standard_name', 'value', 'tropopause_air_pressure')
    
        self.pProcessNcml.changeLocalAttribute('q2', 'units', 'value', 'kg kg-1')
        self.pProcessNcml.changeLocalAttribute('q2', 'standard_name', 'value', 'surface_specific_humidity')
      
        self.pProcessNcml.changeLocalAttribute('ps', 'units', 'value', 'Pa')
        self.pProcessNcml.changeLocalAttribute('ps', 'standard_name', 'value', 'surface_air_pressure')
      
        self.pProcessNcml.changeLocalAttribute('psl', 'units', 'value', 'Pa')
        self.pProcessNcml.changeLocalAttribute('psl', 'standard_name', 'value', 'air_pressure_at_sea_level')
      
        self.pProcessNcml.changeLocalAttribute('glw', 'units', 'value', 'W m-2')
        self.pProcessNcml.changeLocalAttribute('glw', 'standard_name', 'value', 'atmosphere_net_rate_of_absorption_of_longwave_energy')
        
        self.pProcessNcml.changeLocalAttribute('gsw', 'units', 'value', 'W m-2')
        self.pProcessNcml.changeLocalAttribute('gsw', 'standard_name', 'value', 'atmosphere_net_rate_of_absorption_of_shortwave_energy')
        
        return


    def completeMetadataNumpymeta(self):
        "Complete missing data in metadata coordinate XML file manually"
        #--> Nothing to complete at the moment
        return



#_______________________________________________________________________________

def main():
    """
    Main function.

    This function represents the user interface and is called when the
    program is executed. Start the program by executing it with the following
    statement in your shell: grads_2Interface.py --help
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
    pParser.set_defaults(dataType = NUMPYDATA_DTYPE)

    
    pParser.add_option("-c", "--complModel", action="store_true",  dest='completeModel', help="Complete data model by functions particularly written for specific data (default = %default)")
    pParser.add_option("-d", "--doc", action="store_true",  dest='isDoc', help="Give more information by printing docstrings (default = %default)")
    pParser.add_option('-l', '--log', action = 'store', dest='logLevel', choices = ['debug','info','warning','error','critical'], nargs = 1, help="Minimum level for printing information to the console (default = %default)")
    pParser.add_option('-n', '--nodata', action = 'store', dest='nodataValue', nargs = 1, help="Set nodata value (default = %default)")
    pParser.add_option('-p', '--path', action = 'store', type ='string', dest='dataPath', nargs = 1, help="Directory for input / output files (default = %default)")
    pParser.add_option('-s', '--specData', action = 'store', dest='specificData', nargs = 2, help="Only extract specific data as implemented in function 'choseSpecificData' \
        between DATASTART (arg1) and DATASTOP (arg2)") #(default = %default)")
    pParser.add_option('-t', '--dtype', action = 'store', dest='dataType', choices = [''] + NUMPY_DTYPES, nargs = 1, help="Define output data type of numpy array (default = %default)")
    
    (options, args) = pParser.parse_args()


    #Initialize logger
    #-------------------------------------------------------------------------------
    pLog = LoggingInterface(MODULE_LOGGER_ROOT, options.logLevel, pDefaultSettings.loggerLevelFile) #Instance is necessary although if not used.
    pLogger = logging.getLogger(MODULE_LOGGER_ROOT+"."+__name__)
    pLogger.info("_____________________________________________________________________________________________")
    pLogger.info("Starting program 'GRADS2INTERFACE' version '" + str(__version__) + "' from '" + str(__date__) + "':")


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
        pControlModelGrads = ControlModelGrads(infileName, options)

        if operation_ == 'grads2Model':
            pLogger.info("Operation: Convert GRADS to data model")
            pControlModelGrads.writeGradsNumpyData() #Write numpy data array
            pControlModelGrads.writeGradsMetadata() #Write metadata

            if options.completeModel:#optional
                pControlModelGrads.completeDataModelManually() #Complete data model manually

        elif operation_ == 'printGrads':
            pLogger.info("Operation: Print GRADS data on the screen")
            pControlModelGrads.printGradsMetadata()

        elif operation_ == 'testGrads':
            pLogger.info("Operation: Test GRADS functionalities")
            pControlModelGrads.testGradsFunctionality()

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
        
        #pControlModelGrads.__del__()

  
if __name__ == "__main__":
      main()
