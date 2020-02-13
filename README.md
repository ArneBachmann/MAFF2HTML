# MAFF2HTML

This tool converts your MAFF archived websites to single LZMA-compressed base64-encoded HTML files.
The HTML frames referenced by the frameset and all their nested referenced resources like images, stylesheets and scripts are inlined by base64-encoded `data:` URLs.

This approach lets you keep all information in a *single* HTML file, but even modern (year 2020) browsers struggle with frames (generic refresh and redirect bugs) and fail to render base64-encoded contents efficiently.
Load times may be long, memory consumption may be high, and your browser tabs may crash.

Enjoy!
