#!bin/sh

#Batch to convert GDAL readable files to NetCDF: Here LAI products
#__author__= "Nicolai Holzer"
#__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
#__date__ ="2011-04-15"
#__version__ = "v0.1.2" #MajorVersion(backward_incompatible).MinorVersion(backward_compatible).Patch(Bug_fixes)


#Define Input data
DATADIR='data/' #Directory of data
DATAFILES='TIBET_LAI.A*' #Name of data files with or without wildcard
SUFFIX='.hdf'


clear

#Optional: Reproject all GDAL files to data model reprojection
for i in $DATADIR$DATAFILES$SUFFIX
do
    python gdal_2Interface_LAI.py reproject $i -p '' #-b -e -n -l -r
done


#Convert all GDAL files to data model files
for j in $DATADIR$DATAFILES'_repr'$SUFFIX
do
    python gdal_2Interface_LAI.py gdal2Model $j -c -p '' -t int8 -z time #-n -b -l
done


#Optional: Make data variable boolean
#for k in $DATADIR$DATAFILES'__data.npy'
#do
#    python interface_Main.py utilities $k -p '' -b 0 1 #-i -c -m -v -f -l
#done



#Convert all data model files to NetCDF files
for l in $DATADIR$DATAFILES'__data.npy'
do
    python interface_Main.py model2Nc $l -p '' -f '' #-i -c -m -v -l
done


#Optional: Aggregate all NetCDF files to one single NetCDF file
python interface_Main.py nc2Nc $DATAFILES -p $DATADIR -f cf+default #-i -c -m -v -l


#echo `pwd`