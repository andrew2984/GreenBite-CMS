@echo off
set condaEnvPath="./environment.yml"
set envName="greenbite-cms-env"
@echo on

CALL prune_conda_env.bat

echo "updating %envName% from %condaEnvPath%"
conda env update -n=%envName% -f=%condaEnvPath% --prune

echo "Activating conda environment %envName%"
conda activate %envName%

echo "Complete"
