#!bin/sh

#Batch to convert CSV readable files to NetCDF
#__author__= "Nicolai Holzer"
#__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
#__date__ ="2011-01-07"
#__version__ = "v0.1.1" #MajorVersion(backward_incompatible).MinorVersion(backward_compatible).Patch(Bug_fixes)


#Define input data
DATADIR='data/' #Directory of data
DATAFILES='CR10_Lhasa_All*' #Name of data files with or without wildcard
SUFFIX='.csv'


clear

#Convert all CSV files to data model files
for i in $DATADIR$DATAFILES$SUFFIX
do
    python csv_2Interface.py csv2Model $i -c -n -9999 -p '' -s -t float32 -v # -l
done


#Convert all data model files to NetCDF files
for j in $DATADIR$DATAFILES'_time_series__data.npy'
do
    python interface_Main.py model2Nc $j -p '' -f '' #-i -c -m -v -l
done


#Optional: Aggregate all NetCDF files to one single NetCDF file
python interface_Main.py nc2Nc $DATAFILES'_time_series' -p $DATADIR -f cf+default+station #-i -c -m -v -l


#echo `pwd`