CEOP-AEGIS DATA INTERFACE
------------------------------------------------------------------------------------------------------------------------------------------

This program was developed as part of a diploma thesis with topic 'Development of an interface for the conversion of
geodata in a NetCDF data model and publication of this data by the use of the web application DChart, related to the CEOP-AEGIS project'

Additional information can be found in the diploma thesis document.

------------------------------------------------------------------------------------------------------------------------------------------
COPYRIGHT INFORMATION

Nicolai Holzer; 2011
first-name dot last-name @ mailbox.tu-dresden.de

Université de Strasbourg
Laboratoire des Sciences de l’Image, de l’Informatique et de la Télédétecion
- in cooperation with -
Technische Universität Dresden
Fakultät Forst-, Geo und Hydrowissenschaften, Institut für Kartographie


------------------------------------------------------------------------------------------------------------------------------------------
KNOWN BUGS

- String 'Byte' in list BYTE in module 'interface_Settings.py': This string is sometimes necessary for data conversion, but occasionally it 
causes error messages. If this happens, disable string 'Byte' (by setting it in comments). If this string is needed, enable it.
- Type 'float32' for numpy data arrays: Problems in matters of rounding of floating values may occur with this data type. This problem is solved
within the program code by some sort of hacks (see comments in program code).




==========================================================================================================================================
PARSER COMMANDS FOR CEOP-AEGIS DATA INTERFACE

------------------------------------------------------------------------------------------------------------------------------------------
INTERFACE_MAIN

In [8]: %run interface_Main.py --help
Usage: interface_Main.py [options] operation data    
[options]:    
    type '--help' for more information    
    
operation:    
    - model2Nc        Convert one single data model dataset to one single NetCDF file    
    - nc2Nc           Convert one or multiple NetCDF files (by time aggregation) to one single NetCDF file    
    - nc2model        Convert one or multiple NetCDF files (by time aggregation) to one single data model dataset    
    - model2Model     Convert one single data model dataset to one single data model dataset    
    - readModel       Read one single data model dataset with possibility to employ operations on it    
    - readNc          Read one single NetCDF file with possibility to employ operations on it    
    - utilities       Apply special utility operations to the data by setting related options    
    
data:    
    - Filename (with or without .nc-filename extension, with or without wildcards (*)) of a NetCDF file(s) respecting the defined conventions.    
    - Filename (without __*-extension) of a data model dataset respecting the defined conventions.

Data Model Interface for CEOP-AEGIS data conversion in final NetCDF format
Import / Export of data model files and of NetCDF files that respect the
defined conventions

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -b MAKEBOOL, --makebool=MAKEBOOL
                        Utility operation to make booleans for values of data
                        variable #'arg1' by ignoring values 'arg2,..'
  -c, --pcoords         Print values of coordinate variables on screen
                        (default = False)
  -d, --doc             Give more information by printing docstrings (default
                        = False)
  -f CHECKNETCDF, --filecheck=CHECKNETCDF
                        Check a NetCDF file if it is conform to on or more
                        defined conventions (default = cf+default)
  -i NITERATIONS, --iterations=NITERATIONS
                        Number of iterations to employ operation (default = 1)
  -l LOGLEVEL, --log=LOGLEVEL
                        Minimum level for printing information to the console
                        (default = info)
  -m, --pmeta           Print NCML Metadata of data model on screen (default =
                        False)
  -p DATAPATH, --path=DATAPATH
                        Directory for input / output files (default = data/)
  -v, --pvars           Print values of data variables on screen (default =
                        False)

Author: Nicolai Holzer (E-mail: first-name dot last-name @ mailbox.tu-
dresden.de)


------------------------------------------------------------------------------------------------------------------------------------------
GRADS_2INTERFACE

In [9]: %run grads_2Interface.py --help
Usage: grads_2Interface.py [options] operation data    
[options]:    
    type '--help' for more information    
    
operation:    
    - grads2Model     Convert GRADS raster image file (here GRAPES GRIB data) to data model    
    - printGrads      Read GRADS file and print it on screen    
    - testGrads       Test GRADS functionalities    
    
data:    
    Raster data file that is readable by GRADS library

Conversion tool of CEOP-AEGIS data model for GRADS readable raster data

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -c, --complModel      Complete data model by functions particularly written
                        for specific data (default = False)
  -d, --doc             Give more information by printing docstrings (default
                        = False)
  -l LOGLEVEL, --log=LOGLEVEL
                        Minimum level for printing information to the console
                        (default = info)
  -n NODATAVALUE, --nodata=NODATAVALUE
                        Set nodata value (default = 0)
  -p DATAPATH, --path=DATAPATH
                        Directory for input / output files (default = data/)
  -s SPECIFICDATA, --specData=SPECIFICDATA
                        Only extract specific data as implemented in function
                        'choseSpecificData'         between DATASTART (arg1)
                        and DATASTOP (arg2)
  -t DATATYPE, --dtype=DATATYPE
                        Define output data type of numpy array (default =
                        float32)

Author: Nicolai Holzer (E-mail: first-name dot last-name @ mailbox.tu-
dresden.de)


------------------------------------------------------------------------------------------------------------------------------------------
GDAL_2INTERFACE


In [6]: %run gdal_2Interface.py --help
Usage: gdal_2Interface.py [options] operation data    
[options]:    
    type '--help' for more information    
    
operation:    
    - reproject       Reproject image to defined projection and extend    
    - gdal2Model      Convert GDAL raster image file to data model    
    - printGdal       Read GDAL file and print it on screen    
    
data:    
    Raster data file that is readable by the GDAL library

Conversion tool of CEOP-AEGIS data model for GDAL readable raster data

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -b BANDNUMBER, --band=BANDNUMBER
                        Bands from 1 to 'input' on that the operation is to be
                        employed (default = none)
  -c, --complModel      Complete data model by functions particularly written
                        for specific data (default = False)
  -d, --doc             Give more information by printing docstrings (default
                        = False)
  -e EXTENDLIST, --extend=EXTENDLIST
                        Extend for 'reprojection': LatMin, LatMax, LonMin,
                        LonMax (default = [26.52, 39.600000000000001,
                        73.459999999999994, 104.37])
  -l LOGLEVEL, --log=LOGLEVEL
                        Minimum level for printing information to the console
                        (default = info)
  -n NODATAVALUE, --nodata=NODATAVALUE
                        Set nodata value (default = , if default = '' then
                        Dataset nodata value)
  -p DATAPATH, --path=DATAPATH
                        Directory for input / output files (default = data/)
  -r RASTERSIZELIST, --rastersize=RASTERSIZELIST
                        Rastersize for 'reprojection': Y-Rastersize,
                        X-Rastersize (default = [100, 200])
  -t DATATYPE, --dtype=DATATYPE
                        Define output data type of numpy array (default = )
  -v, --nopvars         Beside metadata print also data variable values on
                        screen (default = True)
  -z BANDDIM, --zdim=BANDDIM
                        Define which NetCDF dimension should represent the
                        vertical band of the GDAL file (default = time)

Author: Nicolai Holzer (E-mail: first-name dot last-name @ mailbox.tu-
dresden.de)


------------------------------------------------------------------------------------------------------------------------------------------
CSV_2INTERFACE

In [2]: %run csv_2Interface.py --help
Usage: csv_2Interface.py [options] operation data    
[options]:    
    type '--help' for more information    
    
operation:    
    - csv2Model      Convert CSV table to data model    
    
data:    
    Table as CSV file, with or without variable names in first row

Conversion tool of CEOP-AEGIS data model for CSV table data considered as
station data

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -c, --complModel      Complete data model by functions particularly written
                        for specific data (default = False)
  -d, --doc             Give more information by printing docstrings (default
                        = False)
  -l LOGLEVEL, --log=LOGLEVEL
                        Minimum level for printing information to the console
                        (default = info)
  -n NODATAVALUE, --nodata=NODATAVALUE
                        Set nodata value (default = -9999)
  -p DATAPATH, --path=DATAPATH
                        Directory for input / output files (default = data/)
  -s, --specData        Only extract specific data as implemented in function
                        'choseSpecificData' (default = False)
  -t DATATYPE, --dtype=DATATYPE
                        Define output data type of numpy array (default =
                        float32)
  -v, --varNames        First row in CSV file contains variable names (default
                        = False)

Author: Nicolai Holzer (E-mail: first-name dot last-name @ mailbox.tu-
dresden.de)



