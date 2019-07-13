set "release_name=autosub"
set "package_name=autosub"

cd %~dp0
mkdir "..\.release\%package_name%"
cp "release_files\run.bat" "..\.release\%package_name%"
cp "release_files\help.bat" "..\.release\%package_name%"
cp "release_files\run-with-http-proxy.bat" "..\.release\%package_name%"
cp "..\.build_and_dist\pyinstaller.build\%release_name%.exe" "..\.release\%package_name%"
call update_requirements.bat
cp "..\requirements.txt" "..\.release\%package_name%"
cp "..\README.md" "..\.release\%package_name%"
cp "..\CHANGELOG.md" "..\.release\%package_name%"
cp "..\docs\README.zh-Hans.md" "..\.release\%package_name%"
cp "..\docs\CHANGELOG.zh-Hans.md" "..\.release\%package_name%"
cp "..\LICENSE" "..\.release\%package_name%"
7z a -sdel "..\.release\%release_name%-alpha-win-x64.7z" "..\.release\%package_name%"
%PY_HOME%\python GENERATE.py "..\.release"
call cmd