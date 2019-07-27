#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines release creation scripts.
"""

# Import built-in modules
import os
import sys
import shutil
import subprocess

# Import third-party modules


# Any changes to the path and your own modules


def copytree(src,
             dst,
             symlinks=False,
             ignore=None,
             ext=None):
    if not ext:
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

    else:
        for item in os.listdir(src):
            s = os.path.join(src, item)
            if os.path.isfile(s):
                for ext_item in ext:
                    if not item.endswith(ext_item):
                        continue
                    d = os.path.join(dst, item)
                    shutil.copy2(s, d)


if __name__ == "__main__":
    release_name = "autosub"
    package_name = release_name

    metadata = {}
    os.chdir(os.pardir)
    here = os.getcwd()
    with open(os.path.join(here, package_name, "metadata.py")) as metafile:
        exec(metafile.read(), metadata)

    target = os.path.join(here, ".release", package_name)
    target_nuitka = os.path.join(target, package_name)
    target_data = os.path.join(target_nuitka, "data")
    target_pyi = target + "_pyinstaller"
    target_data_pyi = os.path.join(target_pyi, "data")
    if os.path.isdir(target):
        shutil.rmtree(target)
    os.makedirs(target)
    if os.path.isdir(target_pyi):
        shutil.rmtree(target_pyi)
    os.makedirs(target_pyi)
    p = subprocess.Popen("pipreqs --encoding=utf-8 --force "
                         "--savepath requirements.txt {}".format(package_name),
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    copytree(src=here, dst=target, ext=[".md", ".txt"])
    copytree(src="docs", dst=target, ext=[".md"])
    shutil.copy2("LICENSE", target)
    copytree(src=target, dst=target_pyi)
    shutil.copy2(".build_and_dist/pyinstaller.build/{}.exe".format(release_name), target_pyi)
    copytree(src="scripts/release_files_pyi", dst=target_pyi)

    os.makedirs(target_data)
    os.makedirs(target_data_pyi)
    copytree(src="{}/data".format(package_name), dst=target_data)
    copytree(src="{}/data".format(package_name), dst=target_data_pyi)
    copytree(src=".build_and_dist/{}.dist".format(release_name), dst=target_nuitka)
    copytree(src="scripts/release_files", dst=target)
    output_bytes = subprocess.check_output("7z a -sdel \".release/{release_name}-{version}-win-x64.7z\" "
                                           "\"{target}\"".format(release_name=release_name,
                                                                 version=metadata['VERSION'],
                                                                 target=target),
                                           stdin=open(os.devnull),
                                           shell=False)
    output_str = output_bytes.decode(sys.stdout.encoding)
    print(output_str)

    output_bytes = subprocess.check_output("7z a -sdel \".release/{release_name}-{version}-win-x64-pyinstaller.7z\" "
                                           "\"{target_pyi}\"".format(release_name=release_name,
                                                                     version=metadata['VERSION'],
                                                                     target_pyi=target_pyi),
                                           stdin=open(os.devnull),
                                           shell=False)
    output_str = output_bytes.decode(sys.stdout.encoding)
    print(output_str)

    output_bytes = subprocess.check_output("python scripts/generate_sha256.py .release",
                                           stdin=open(os.devnull),
                                           shell=False)
    output_str = output_bytes.decode(sys.stdout.encoding)
    print(output_str)
    input("输入任何字符以退出：")
