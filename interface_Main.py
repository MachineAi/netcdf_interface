#! /usr/bin/python
# -*- coding: latin1 -*-

"""
Main Modul.

This module represents the user interface and provides specific functions for
operations on data that can be executed by the user. Find more information in the documentation.
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-03-28"
__version__ = "v0.1.2" #MajorVersion(backward_incompatible).MinorVersion(backward_compatible).Patch(Bug_fixes)


#Changelog
#-------------------------------------------------------------------------------
#2011-01-14: v0.1.2 logging implemented, functionality changed
#2010-11-23: v0.1.1 comments and docstrings added
#2010-10-08: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
import sys
from optparse import OptionParser
import logging

#related libraries
#local applications / library specific import
from interface_Settings import *
from interface_Control import *

#===============================================================================


#Module constants (Parser)
#-------------------------------------------------------------------------------
USAGE = "Usage: %prog [options] operation data\
    \n[options]:\
    \n    type '--help' for more information\
    \n\
    \noperation:\
    \n    - model2Nc        Convert one single data model dataset to one single NetCDF file\
    \n    - nc2Nc           Convert one or multiple NetCDF files (by time aggregation) to one single NetCDF file\
    \n    - nc2model        Convert one or multiple NetCDF files (by time aggregation) to one single data model dataset\
    \n    - model2Model     Convert one single data model dataset to one single data model dataset\
    \n    - readModel       Read one single data model dataset with possibility to employ operations on it\
    \n    - readNc          Read one single NetCDF file with possibility to employ operations on it\
    \n    - utilities       Apply special utility operations to the data by setting related options\
    \n\
    \ndata:\
    \n    - Filename (with or without .nc-filename extension, with or without wildcards (*)) of a NetCDF file(s) respecting the defined conventions.\
    \n    - Filename (without __*-extension) of a data model dataset respecting the defined conventions."

DESCRIPTION= "Data Model Interface for CEOP-AEGIS data conversion in final NetCDF format\
    \nImport / Export of data model files and of NetCDF files that respect the defined conventions"

EPILOG = "Author: "+__author__+" (E-mail: "+__author_email__+")"

VERSION = "%prog version "+__version__+" from "+__date__


#Module default values / constants, may be overwritten by OptionParser
#-------------------------------------------------------------------------------
#--> See module interface_Settings



#_______________________________________________________________________________

class MainInterface:
    """
    Main class for data interface.

    Class containing functions for operations on data by the use of this data
    interface. The module 'interface_Control' provides all possible operations to this class.

    COMMENTS:
    Suffixes will be automatically assigned and must respect the declarations
    in the module 'interface_Settings'.

    IMPORTANT:
    All input files of the data model must be coherent to each other and respect the
    specifications. Please refer to the documentation or to additional information
    in the docstrings of the specific functions in case of questions or if problems occure.
    """

    def __init__(self, option_):
        """Constructor"""
        self.pParserOptions = option_
        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)
        self.pLogger.info("_____________________________________________________________________________________________")
        self.pLogger.info("Starting program 'INTERFACE' version '" + str(__version__) + "' from '" + str(__date__) + "':")
     

    #def __del__ (self):
        #"""Destructor"""
     

    def dataModel2NetCdf(self, infile_):
        """
        Converts data from the data model to NetCDF.
        
        This function converts data from the data model (numpy data array, coordinate metadata xml file and
        NCML NetCDF XML file) to a new NetCDF file. 
        
        INPUT_PARAMETERS:
        infile      - Name of data files without suffixes (string)
        """

        self.pLogger.info("Operation: Convert data model to NetCDF")

        pControl = ControlModel(infile_, self.pParserOptions)
        pControl.readMetadataNcml()
        pControl.readDataNumpy()
        
        pControl.printModel() #Optional if parser option is set

        pControl.writeNetCdf()

        pControl.checkNetCdf() #Optional if parser option is set

        #pControl.__del__()
        return


    def netCdf2NetCdf(self, infile_):
        """
        Converts one or multiple NetCDF files to a NetCDF file.
        
        This function converts one or multiple NetCDF files to a new NetCDF file.
        In case that multiple NetCDF files are read, an new NetCDF file will be created
        by aggregating the input data (time aggregation).
        
        INPUT_PARAMETERS:
        infile      - NetCDF file name without suffix (string) or that part of the
            NetCDF file name that is shared by all files (for reading multiple files).

        COMMENTS:
        For reading and aggregating multiple NetCDF files all files need to be similiar
        expect of the time coordinate values (but need to share the same time unit).
        """

        self.pLogger.info("Operation: Convert NetCDF to NetCDF (Might be time consuming in case of aggregation!)")

        pControl = ControlModel(infile_, self.pParserOptions)
        pControl.readNetCdf()

        pControl.printModel() #Optional if parser option is set
        
        pControl.writeNetCdf()

        pControl.checkNetCdf() #Optional if parser option is set

        #pControl.__del__()
        return


    def netCdf2DataModel(self, infile_):
        """
        Converts one or multiple NetCDF files to the data model
        
        This function converts one or multiple NetCDF files to the data model 
        (numpy data array, coordinate metadata xml file and NCML NetCDF XML file)
        
        INPUT_PARAMETERS:
        infile      - NetCDF file name without suffix (string) or that part of the
            NetCDF file name that is shared by all files (for reading multiple files).
        
        COMMENTS:
        For reading and aggregating multiple NetCDF files all files need to be similiar
        expect of the time coordinate values (but need to share the same time unit).
        """

        self.pLogger.info("Operation: Convert NetCDF to data model")

        pControl = ControlModel(infile_, self.pParserOptions)

        pControl.readNetCdf()

        pControl.printModel() #Optional if parser option is set
        pControl.checkNetCdf() #Optional if parser option is set

        pControl.writeMetadataNcml()
        pControl.writeDataNumpy()

        #pControl.__del__()
        return


    def dataModel2DataModel(self, infile_):
        """
        Converts data from the data model back to the data model.

        This function converts data from the data model (numpy data array, coordinate metadata xml file and
        NCML NetCDF XML file) back to the data model.

        INPUT_PARAMETERS:
        infile      - Name of data files without suffixes (string)
        """

        self.pLogger.info("Operation: Convert data model to data model")

        pControl = ControlModel(infile_, self.pParserOptions)
        pControl.readMetadataNcml()
        pControl.readDataNumpy()

        pControl.printModel() #Optional if parser option is set
        
        pControl.writeMetadataNcml()
        pControl.writeDataNumpy()

        #pControl.__del__()
        return


    def readModel(self, infile_):
        """
        Read data from the data model with the possibility to employ operations on it.

        INPUT_PARAMETERS:
        infile      - Name of data files without suffixes (string)
        """

        self.pLogger.info("Operation: Read data model")

        pControl = ControlModel(infile_, self.pParserOptions)
        pControl.readMetadataNcml()
        pControl.readDataNumpy()

        pControl.printModel() #Optional if parser option is set
      
        #pControl.__del__()
        return


    def readNetCdf(self, infile_):
        """
        Read one or multiple NetCDF files with the possibility to employ operations on it.

        INPUT_PARAMETERS:
        infile      - NetCDF file name without suffix (string) or that part of the
            NetCDF file name that is shared by all files (for reading multiple files).

        COMMENTS:
        For reading and aggregating multiple NetCDF files all files need to be similiar
        expect of the time coordinate values (but need to share the same time unit).
        """

        self.pLogger.info("Operation: Read NetCDF")

        pControl = ControlModel(infile_, self.pParserOptions)
        pControl.readNetCdf()

        pControl.printModel() #Optional if parser option is set
        pControl.checkNetCdf() #Optional if parser option is set

        #pControl.__del__()
        return

    
    def utilities(self, infile_):
        """
        Various utility options to modify the data model

        INPUT_PARAMETERS:
        infile      - Name of data files (data model) without suffixes (string)

        COMMENTS:
        This utilities can be called if the input operation argument is set to
        'utilities' and if the a option with its related arguments is choosen
        """

        self.pLogger.info("Operation: Apply interface utilities")

        pControl = ControlModel(infile_, self.pParserOptions)

        #Optional if parser option is set
        if not self.pParserOptions.makeBool is None: #Option makeBool is choosen
            pControl.makeNumpyVarBool()
       
        else: #If no option is choosen print information of all available utility options
            self.pLogger.info("Set utilitity parser options [-b] with corresponding arguments to use this function.")

        #pControl.__del__()
        return


    def test(self):
        """Temporary test"""

        import numpy
        print '\ntest\n'

        pNumpy = numpy.arange(25.0, 43.0, numpy.float32(0.3), dtype = numpy.float32)
        pNumpy = numpy.arange(25, 43, 0.3)
        #pNumpy = numpy.linspace(25, 43, 61)
        pNumpy = pNumpy.astype(numpy.float32)
        #numpy.cast['float32'](pNumpy)
        #pNumpy = numpy.around(pNumpy, decimals = 0)
        print pNumpy
        print pNumpy.dtype

        #for shape in range(0,pNumpy.shape[0],1):
        #            value = pNumpy[shape]
        #            value = round(value,2)
        #            value = numpy.float32(value)
        #            print value
        #            print value.dtype
        #            pNumpy1[shape] = value

        #pNumpy = pNumpy1.astype(numpy.float32)
        #print pNumpy
        #print pNumpy.dtype

        #pNumpy2 = numpy.empty(61, dtype=numpy.float32)
        return
    


#_______________________________________________________________________________

def main():
    """
    Main function.

    This function represents the user interface and is called when the interface
    program is executed. For more information about the usage execute this program
    with the following statement in your shell: interface_Main.py --help
    """

    startTime = time.time()
    pDefaultSettings = DefaultSettings()
    
    #Parser definition
    #-------------------------------------------------------------------------------
    pParser = OptionParser(usage=USAGE, version = VERSION, description = DESCRIPTION, epilog = EPILOG)
   
    pParser.set_defaults(printCoords = False)
    pParser.set_defaults(isDoc = False)
    pParser.set_defaults(checkNetCdf = pDefaultSettings.checkData)
    pParser.set_defaults(nIterations = 1)
    pParser.set_defaults(logLevel = pDefaultSettings.loggerLevelConsole)
    pParser.set_defaults(printMeta = False)
    pParser.set_defaults(dataPath = pDefaultSettings.dataDirectory) 
    pParser.set_defaults(printVars = False)


    pParser.add_option("-b", "--makebool", action = 'store', dest='makeBool', nargs = 2, help="Utility operation to make booleans for values of data variable #'arg1' by ignoring values 'arg2,..'")# (default = %default)")
    pParser.add_option("-c", "--pcoords", action="store_true",  dest='printCoords', help="Print values of coordinate variables on screen (default = %default)")
    pParser.add_option("-d", "--doc", action="store_true",  dest='isDoc', help="Give more information by printing docstrings (default = %default)")
    pParser.add_option("-f", "--filecheck", action = 'store', dest='checkNetCdf', choices = ['','cf','default','station','cf+default','cf+default+station'], nargs = 1, help="Check a NetCDF file if it is conform to on or more defined conventions (default = %default)")
    pParser.add_option('-i', '--iterations', action = 'store', type ='int', dest='nIterations', nargs = 1, help="Number of iterations to employ operation (default = %default)")
    pParser.add_option('-l', '--log', action = 'store', dest='logLevel', choices = ['debug','info','warning','error','critical'], nargs = 1, help="Minimum level for printing information to the console (default = %default)")
    pParser.add_option("-m", "--pmeta", action="store_true",  dest='printMeta', help="Print NCML Metadata of data model on screen (default = %default)")
    pParser.add_option('-p', '--path', action = 'store', type ='string', dest='dataPath', nargs = 1, help="Directory for input / output files (default = %default)")
    pParser.add_option("-v", "--pvars", action="store_true",  dest='printVars', help="Print values of data variables on screen (default = %default)")

    (options, args) = pParser.parse_args()


    #Initialize logger
    #-------------------------------------------------------------------------------
    pLog = LoggingInterface(INTERFACE_LOGGER_ROOT, options.logLevel, pDefaultSettings.loggerLevelFile) #Instance is necessary although if not used.
    pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__)


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
        #Print Docstrings
        if options.isDoc:
            pLogger.info(__doc__)
            sys.exit(0)

        dataPath = options.dataPath
        if not dataPath.endswith('/') and dataPath != '': #Adds '/' to path in case that this is not the case
            dataPath = dataPath+'/'
        infileName = dataPath+infile_ #Add path of data directory to filename


        #Run program
        #-------------------------------------------------------------------------------
        pInterfaceMain = MainInterface(options) #Initialize

        for i in range(0,options.nIterations,1):
            pLogger.debug("Number of iterations: '" + str(i) + "'")

            #pInterfaceMain.test()

            if operation_ == 'model2Nc':
                pInterfaceMain.dataModel2NetCdf(infileName)
            elif operation_ == 'nc2Nc':
                pInterfaceMain.netCdf2NetCdf(infileName)
            elif operation_ == 'nc2Model':
                pInterfaceMain.netCdf2DataModel(infileName)
            elif operation_ == 'model2Model':
                pInterfaceMain.dataModel2DataModel(infileName)

            elif operation_ == 'readModel':
                pInterfaceMain.readModel(infileName)
            elif operation_ == 'readNc':
                pInterfaceMain.readNetCdf(infileName)

            elif operation_ == 'testAll':
                pInterfaceMain.dataModel2NetCdf(infileName)
                pInterfaceMain.netCdf2NetCdf(infileName)
                pInterfaceMain.netCdf2DataModel(infileName)
                pInterfaceMain.dataModel2DataModel(infileName)

            elif operation_ == 'utilities':
                pInterfaceMain.utilities(infileName)

            else:
                pLogger.error("Parser error: Operation '" + str(operation_) + "' is unknown.")
                pParser.error("Operation '" + str(operation_) + "' is unknown.") #System exit code 2


    except Exception: #If exceptiation occured in this module or all connected sub-modules
        pLogger.exception('Exception Error occured: ')
        raise

    finally:
        pLogger.info("Finished. Total processing time [s]: '" + str(time.time() - startTime) + "'.")
        pLogger.info("_____________________________________________________________________________________________")
        pLog.__del__()

        # pInterfaceMain.__del__()


if __name__ == "__main__":
      main()    