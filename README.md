# MAFF2HTML

This tool converts your MAFF archived websites to single base64-encoded HTML files, optionally compressed via LZMA or BZip2.

The HTML frames referenced by the MAFF's frameset and all their nested referenced resources like images, stylesheets, fonts and scripts are inlined using base64-encoded `data:` URLs (!).

This unique approach lets you keep all information of the MAFF in a *single* HTML file.
Sadly, however, even modern (year 2020) browsers struggle with larger HTML documents with frames and inline data and may fail to render base64-encoded contents efficiently, or crash with out of memory errors.

Anyway I think this is a uniquely useful approach to keeping your data while not relying on plugins to display your archived web pages.

Enjoy!


## Usage
The basic command `python[3] maff2html.py [--compress [--lzma]]` will find any `*.maff` files in the current and all sub-directories and convert them into `*.html.xz`, `*.html.bz2` or `*.maff.html` file (depending on the chosen compression option), leaving the original `*.maff` file untouched.
