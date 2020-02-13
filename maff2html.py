''' MAFF2HTML converter  (C) 2020  Arne Bachmann  https://github.com/ArneBachmann/maff2html '''

# HINT Optional libraries: pip[3] install filetype python-magic
# TODO instead of unzipping into temporary folders (very bad on Windows)=, unzip in memory instead

import base64, bz2, imghdr, lzma, mimetypes, os, pathlib, re, shutil, sys, tempfile, urllib.parse, zipfile
try: import filetype
except: pass
try: import magic
except: pass

titleRE =    re.compile(b'<MAF:title RDF:resource="(.*?)"')
originalRE = re.compile(b'<MAF:originalurl RDF:resource="(.*?)"')
charsetRE =  re.compile(b'<MAF:charset RDF:resource="(.*?)"')
indexRE =    re.compile(b'<MAF:indexfilename RDF:resource="(.*?)"/>')
datetimeRE = re.compile(b'<MAF:archivetime RDF:resource="(.*?)"/>')
refRE =      re.compile(b'"(index_files/.*?)"')

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

# Main frameset
FRAME = b'''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN"
"http://www.w3.org/TR/html4/frameset.dtd">
<html>
  <head>
    <meta http-equiv="Content-type" content="text/html;charset="{charset}">
    <meta http-equiv="Access-Control-Allow-Origin" content="*">
    <title>{title}</title>
  </head>
  <frameset rows="5%,*">
    <frame name="meta"    src="data:text/html;base64, {meta}"  />
    <frame name="content" src="data:text/html;base64, {frame}" />
    <noframes><body><p>Frames required</body></p></noframes>
  </frameset>
</html>
'''

# Metadata frame
META_FRAME = b'''<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="Content-type" content="text/html;charset="{charset}">
    <meta http-equiv="Access-Control-Allow-Origin" content="*">
    <title>{title}</title>
  </head>
  <body style="background-color: gray;">
    <p style="margin:0;line-height:1;">Origin: <a href="{url}">{url}</a></p>
    <p style="margin:0;line-height:1;">Archived: {datetime}</p>
  </body>
</html>
'''


def convertMaffToHtml(sourcefile, targetfile):
  ''' Operating in bytes. '''
  print("Converting " + sourcefile)
  tmp = tempfile.mkdtemp()
  try:
    with zipfile.ZipFile(sourcefile, 'r') as z: z.extractall(tmp)
  except zipfile.BadZipFile: print("  Wrong file format for MAFF '%s'" % sourcefile); return
  base = list(pathlib.Path(tmp).glob("*"))[0]  # only one folder expected
  with open(os.path.join(base, 'index.rdf'),  'rb') as fd: data = fd.read()
  charset  = charsetRE .findall(data)[0]
  title    = titleRE   .findall(data)[0]
  original = originalRE.findall(data)[0]
  index    = indexRE   .findall(data)[0]
  try: datetime = datetimeRE.findall(data)[0]
  except: datetime = "Unknown"
  with open(os.path.join(base, index.decode("utf-8")), 'rb') as fd: main = fd.read()
  groups = refRE.findall(main)
  replacements = {}
  for ref in groups:  # first pass: create replacements
    ref, anchor = (bytes(ref), b"") if b"#" not in bytes(ref) else bytes(ref).split(b"#")[:2]
    if ref in replacements: continue  # already replaced
    file = base / urllib.parse.unquote(ref.decode(charset.decode("ascii")))
    try:
      with open(file, 'rb') as fd: data = fd.read()  # load referenced data file
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
    if mime is None: mime = b"application/octet-stream"; print("  Could not determine file type: " + ref.decode(charset.decode("ascii")))  #; sys.exit(1)
    else: mime = mime.encode(charset.decode("ascii"))
    replacements[ref] = b"data:%s;base64, %s" % (mime, base64.b64encode(data))
  for ref, replacement in replacements.items():  # second pass: perform replacements
    main = main.replace(ref, replacement)  # replace resource link by inlined base64 data
  with ((lzma.LZMAFile(targetfile, 'wb', format = lzma.FORMAT_XZ, check = lzma.CHECK_CRC32, preset = 9) if '--lzma' in sys.argv else bz2.BZ2File(targetfile, 'w')) if '--compress' in sys.argv else open(targetfile, 'wb')) as fd:
    fd.write(FRAME.replace(b"{charset}", charset).replace(b"{title}", title).replace(b"{frame}", base64.b64encode(main)).replace(b"{meta}", base64.b64encode(META_FRAME.replace(b"{charset}", charset).replace(b"{url}", original).replace(b"{title}", title).replace(b"{datetime}", datetime))))
  shutil.rmtree(tmp)
  try: os.unlink(sourcefile.replace(".maff", ".html"))
  except: pass


if __name__ == '__main__':
  if '--help' in sys.argv:
    print("python[3] maff2html.py [--compress [--lzma]]")
  for dirname, dirpaths, filepaths in os.walk(os.path.abspath(os.getcwd())):
    for filename in (f for f in filepaths if f.endswith(".maff")):
      convertMaffToHtml(os.path.join(dirname, filename), os.path.join(dirname, filename.replace(".maff", ((".html.xz" if "--lzma" in sys.argv else ".html.bz2") if '--compress' in sys.argv else '.maff.html'))))
