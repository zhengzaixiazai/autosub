@echo off
set nuitka_build_bat_name="nuitka_build.bat"
set log_name="%date:~0,4%_%date:~5,2%_%date:~8,2%_%time:~0,2%_%time:~3,2%_%time:~6,2%_build.log"
set output_dir="../.build_and_dist/"
set icon_dir="../docs/icon/autosub.ico"
set package_name="autosub"

@echo on
cd %~dp0
call nuitka "../%package_name:~1,-1%" --standalone --output-dir %output_dir% --show-progress --show-scons --show-modules --windows-icon=%icon_dir% --plugin-enable=multiprocessing --force-dll-dependency-cache-update --lto --generate-c-only 1>%log_name% 2>&1 3>&1
pause>nul