# MAFF2HTML

This tool converts your MAFF archived websites to single base64-encoded HTML files, optionally compressed via LZMA or BZip2.

The HTML frames referenced by the MAFF's frameset and all their nested referenced resources like images, stylesheets, fonts and scripts are inlined using base64-encoded `data:` URLs (!).

This unique approach lets you keep all information of the MAFF in a *single* HTML file.
I don't think, this solution exists anywhere else.

Sadly, however, even modern (year 2020) browsers struggle loading larger HTML documents with frames and inline data, and may fail to render base64-encoded contents efficiently, or crash with *out of memory* errors.

Anyway I think this is a uniquely useful long-term solution for keeping your data without relying on browser-plugins to display your archived web pages.

Enjoy!


## Usage
The basic usage is:

```bash
python[3] maff2html.py [--compress [--lzma]]
```

This will find all `*.maff` files in the current and all sub-folders and convert them into `*.html.xz`, `*.html.bz2` or `*.maff.html` files, leaving the original `*.maff` file untouched.

| Command-line options | Compression | File extension |
| -------------------- | ----------- | -------------- |
| *none*               | *none*      | `.maff.html`   |
| `--compress`         | BZIP2       | `.html.bz2`    |
| `--compress --lzma`  | LZMA        | `.html.xz`     |
