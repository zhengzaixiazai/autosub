@echo off
set output_dir="../.build_and_dist_win32/"
set icon_dir="../docs/icon/autosub.ico"
set package_name="autosub"

@echo on
cd %~dp0
call update_requirements.bat
cd ..\
pip install -r requirements.txt
cd scripts
nuitka "../%package_name:~1,-1%" --standalone --output-dir %output_dir% --show-progress --show-scons --show-modules --windows-icon=%icon_dir% --recurse-to=multiprocessing --plugin-enable=multiprocessing --lto --assume-yes-for-downloads --python-arch=x86