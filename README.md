SyncTeX backwards search
========================

Example: `evince_synctex.py -v file.pdf -- gvim %f +%l`

Launches Evince to `file.pdf`. If the LaTeX source was compiled with
`--synctex=1`, then you can Ctrl-Click a word in Evince to launch GVim to the
corresponding line in the source.

You can pass a TeX source file to `-s` (`--build-source`)
to run `latexmk --synctex=1 -pvc -view=none -pdf` on the source file,
that is, to continuously build the source file in the background.

Tip: If you want to run Vim in the terminal, continuously build the source file,
and center the line in the Vim window when Vim is launched, use
`evince_synctex.py -s file.tex -v file.pdf -- gnome-terminal --window -- vim %f +%l +'norm zz'`,
or simply run the included helper `latexedit file.tex`.

Based on [gauteh/vim-evince-synctex](https://github.com/gauteh/vim-evince-synctex).
