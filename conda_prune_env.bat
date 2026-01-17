@echo off
set condaEnvPath="./environment.yml"
set envName="greenbite-cms-env"
@echo on

echo "updating %envName% from %condaEnvPath%"
cmd conda env update -n=%envName% -f=%condaEnvPath% --prune

echo "Activating conda environment %envName%"
conda activate %envName%

echo "Complete"

exit
