from hashlib import md5
from mediamgr.models import *
import os
from PIL import ExifTags, Image
import sys


def getPILMetaData (metadata: dict, dirname: str, filename: str) -> dict:
    img = Image.open(os.path.join(dirname, filename))
    exif = img.getexif()
    metadata['exif'] = { ExifTags.TAGS[k]: repr(v) for k, v in exif.items() }
    metadata['format'] = img.format
    metadata['format_description'] = img.format_description
    metadata['height'] = img.height
    metadata['mimetype'] = img.get_format_mimetype()
    metadata['size'] = list(img.size)   # convert from tuple
    metadata['width'] = img.width
    metadata['xmp'] = img.getxmp()
    return metadata


def process_image_file (md: MediaDocument, dirname: str, filename: str) -> dict:
    hash_md5 = md5()
    with open(os.path.join(dirname, filename), "rb") as f:
        for chunk in iter(lambda: f.read(256*1024), b""):
            hash_md5.update(chunk)
    
    hash = hash_md5.hexdigest()
    media = md.get(hash)
    if media is not None:
        print(f"{hash} - Already registered")
        return(media)
    
    metadata = {'hash_md5': hash}

    getPILMetaData(metadata, dirname, filename)

    md.setDocument(metadata)
    md.setKey(hash)
    md.save()

    print(f"{hash} -- added")

    return md.document


def main (argv: list=sys.argv):
    db = connect()
    md = MediaDocument(db)
    dirname = argv[1]
    for filename in os.listdir(dirname):
        process_image_file(md, dirname, filename)
    sys.exit(0)