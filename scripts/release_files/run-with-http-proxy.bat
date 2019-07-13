@echo off
set http_proxy=http://127.0.0.1:1080
set https_proxy=http://127.0.0.1:1080
set package_name=autosub
set "file_name="
rem input your file name between '=' and '"'
@echo on
.\%package_name% -S en-US "%file_name%"
call cmd