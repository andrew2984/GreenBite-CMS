@echo off
set condaEnvPath="./environment.yml"
set envName="greenbite-cms-env"
@echo on

start /wait conda env create -f environment.yml

echo "Activating conda environment %envName%"
conda activate %envName%

echo "Complete"

exit