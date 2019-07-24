cd ..\
xgettext autosub\options.py -L Python -d autosub.options.new -p data\locale\zh_CN\LC_MESSAGES
msgmerge data\locale\zh_CN\LC_MESSAGES\autosub.options.po data\locale\zh_CN\LC_MESSAGES\autosub.options.new.po -U
msgfmt data\locale\zh_CN\LC_MESSAGES\autosub.options.po -o data\locale\zh_CN\LC_MESSAGES\autosub.options.mo
rem rm data\locale\zh_CN\LC_MESSAGES\autosub.options.new.po