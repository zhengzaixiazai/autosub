@echo off
set package_name=autosub
set "file_name="
rem input your file name between '=' and '"'
@echo on
cd %package_name%
.\%package_name% -S en-US -hsp -i "%file_name%"
call cmd