@echo off
set package_name=autosub
@echo on
%~d0
cd %~dp0%
%package_name% -h
pause