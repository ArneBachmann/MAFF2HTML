''' MAFF2HTML converter  (C) 2020-2021  Arne Bachmann  https://github.com/ArneBachmann/maff2html '''
'''                         Pepe Pardo '''
# HINT Optional libraries: pip[3] install filetype python-magic
# TODO instead of unzipping into temporary folders (very bad on Windows), unzip in memory instead
import base64, bz2, imghdr, lzma, mimetypes, os, pathlib, re, shutil, sys, tempfile, urllib.parse, zipfile, html
try: import filetype
except: pass
try: import magic
except: pass

titleRE = re.compile(b'<MAF:title RDF:resource="(.*?)"')
originalRE = re.compile(b'<MAF:originalurl RDF:resource="(.*?)"')
charsetRE = re.compile(b'<MAF:charset RDF:resource="(.*?)"')
indexRE = re.compile(b'<MAF:indexfilename RDF:resource="(.*?)"/>')
datetimeRE = re.compile(b'<MAF:archivetime RDF:resource="(.*?)"/>')
refRE = re.compile(b'"(index_files/.*?)"')

# MIME detection libraries:
# - https://docs.python.org/3/library/imghdr.html
# - https://www.sitepoint.com/mime-types-complete-list/
# - https://en.wikipedia.org/wiki/Graphics_file_format_summary
IMGHDR = {
    'rgb':  'image/x-rgb',
    'gif':  'image/gif',
    'pbm':  'image/x-portable-bitmap',
    'pgm':  'image/x-portable-graymap',
    'ppm':  'image/x-portable-pixmap',
    'tiff': 'image/tiff',
    'rast': 'image/cmu-raster',
    'xbm':  'image/x-xbitmap',
    'jpeg': 'image/jpeg',
    'bmp':  'image/bmp',
    'png':  'image/png',
    'webp': 'image/webp',
    'exr':  'image/exr'
}

SAVEPAGE = rb'''
<div id="savepage-pageinfo-bar-container">
<style id="savepage-pageinfo-bar-style" type="text/css">#savepage-pageinfo-bar-content,#savepage-pageinfo-bar-content *{all:initial!important}#savepage-pageinfo-bar-content,#savepage-pageinfo-bar-content *{font-family:"Segoe UI","Helvetica Neue",Ubuntu,Arial!important;font-size:12px!important;color:black!important;cursor:default!important;-moz-user-select:none!important;-webkit-user-select:none!important}#savepage-pageinfo-bar-content{display:flex!important;position:fixed!important;left:0!important;top:0!important;width:100%!important;height:25px!important;border-bottom:1px solid #E0E0E0!important;background:#F8F8F8!important;overflow:hidden!important;z-index:2147483645!important}#savepage-pageinfo-bar-spacer-1{flex:0 1 auto!important;background:#F8F8F8!important}#savepage-pageinfo-bar-link{flex:0 1 auto!important;padding:4px 0!important;background:#F8F8F8!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}#savepage-pageinfo-bar-link:hover{text-decoration:underline!important}#savepage-pageinfo-bar-spacer-2{flex:1 1 auto!important;background:#F8F8F8!important}#savepage-pageinfo-bar-datetime{flex:0 1000000 auto!important;min-width:0!important;padding:4px 0!important;background:#F8F8F8!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}#savepage-pageinfo-bar-spacer-3{flex:0 1 auto!important;background:#F8F8F8!important}#savepage-pageinfo-bar-button{flex:0 0 25px!important;background-color:#F8F8F8!important;background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJCAYAAADgkQYQAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAA8SURBVChTYwCC/0DsAGJgASBxkDycga4QQxxdAEMBDCBLYFUAAyQpIGgVCGAoxBCAAhRxrEZDAVCc4T8AbzkX8F/+uCwAAAAASUVORK5CYII=)!important;background-repeat:no-repeat!important;background-position:center center!important}#savepage-pageinfo-bar-button:hover{background-color:#E8E8E8!important}#savepage-pageinfo-bar-button:active{background-color:#D8D8D8!important}</style>
<div id="savepage-pageinfo-bar-content">
 <div id="savepage-pageinfo-bar-spacer-1">&nbsp;&nbsp;&nbsp;</div>
 <div id="savepage-pageinfo-bar-spacer-1">{title}</div>
 <div id="savepage-pageinfo-bar-spacer-1">&nbsp;&nbsp;&nbsp;</div>
 <a id="savepage-pageinfo-bar-link" href="{url}" target="_blank">{url}</a>
 <div id="savepage-pageinfo-bar-spacer-2">&nbsp;&nbsp;&nbsp;</div>
 <div id="savepage-pageinfo-bar-datetime">{datetime}</div>
 <div id="savepage-pageinfo-bar-spacer-3">&nbsp;&nbsp;&nbsp;</div>
 <div id="savepage-pageinfo-bar-button" onclick="{document.getElementById('savepage-pageinfo-bar-container').style.display='none';}"></div>
</div>
</div>
</html>
'''

def convertMaffToHtml(sourcefile, targetfile):
    ''' Operating on bytes. '''
    print("Converting '%s'" % sourcefile)
    try:
        with zipfile.ZipFile(sourcefile, 'r') as z:
            lista=z.namelist()
            base=lista[0]
            # Obtener los datos del index .rdf
            data = z.read(base+'index.rdf')
            charset = charsetRE .findall(data)[0]
            title = titleRE   .findall(data)[0]
            original = originalRE.findall(data)[0]
            index = indexRE   .findall(data)[0]
            # Datetime puede venir o no
            try:
                datetime = datetimeRE.findall(data)[0]
            except:
                datetime = "Unknown"
            # Obtener el archivo principal
            main = z.read(base+index.decode("utf-8"))
            groups = refRE.findall(main)
            replacements = {}
            for ref in groups:  # first pass: create replacements
                ref, anchor = (bytes(ref), b"") if b"#" not in bytes(ref) else bytes(ref).split(b"#")[:2]
                if ref in replacements:
                    continue  # already replaced
                file = base + html.unescape(urllib.parse.unquote(ref.decode(charset.decode("ascii"))))
                try: data = z.read(file)  # load referenced data file
                except: print("  Cannot load file '%s'" % ref.decode(charset.decode("ascii"))); continue
                mime = None
                for r in (
                    ref.decode(charset.decode("ascii")),
                    ref.decode(charset.decode("ascii")).replace("_", ".")
                ):
                    if r.endswith(".js"): mime = 'text/javascript'; break
                    try: mime = mimetypes.guess_type(r)[0]
                    except:
                        try: mime = IMGHDR[imghdr.what(file)]  # built-in image type detection
                        except:
                            try: mime = filetype.guess(file)  # able to guess font types like .woff
                            except:
                                try: mime = magic.from_file(file, mime = True)
                                except: pass
                if mime is None: mime = b"application/octet-stream"; print("  Could not determine file type: '%s'" % file)  #; sys.exit(1)
                else: mime = mime.encode(charset.decode("ascii"))
                replacements[ref] = b"data:%s;base64, %s" % (mime, base64.b64encode(data))
            
    except zipfile.BadZipFile:
        print("  Wrong file format for MAFF '%s'" % sourcefile)
        return
    for ref, replacement in replacements.items():  # second pass: perform replacements
        main = main.replace(ref, replacement)  # replace resource link by inlined base64 data
    with ((lzma.LZMAFile(targetfile, 'wb', format = lzma.FORMAT_XZ, check = lzma.CHECK_CRC32, preset = 9) if '--lzma' in sys.argv else bz2.BZ2File(targetfile, 'w')) if '--compress' in sys.argv else open(targetfile, 'wb')) as fd:
        div=SAVEPAGE.replace(b"{title}", title).replace(b"{url}", original).replace(b"{title}", title).replace(b"{datetime}", datetime)
        fd.write(main.replace(b"</html>",div))
        #fd.write(FRAME.replace(b"{charset}", charset).replace(b"{title}", title).replace(b"{frame}", base64.b64encode(main))
        # .replace(b"{meta}", base64.b64encode(META_FRAME.replace(b"{charset}", charset).replace(b"{url}", original).replace(b"{title}", title).replace(b"{datetime}", datetime))))




'''Funcion principal'''
if __name__ == '__main__':
    if '--help' in sys.argv:
        print("python[3] maff2html.py [--compress [--lzma]]")
    for dirname, dirpaths, filepaths in os.walk(os.path.abspath(os.getcwd())):
        for filename in (f for f in filepaths if f.endswith(".maff")):
            target = os.path.join(dirname, filename.replace(".maff", ((
                ".html.xz" if "--lzma" in sys.argv else ".html.bz2") if '--compress' in sys.argv else '.maff.html')))
            if not os.path.exists(target):
                convertMaffToHtml(os.path.join(dirname, filename), target)
