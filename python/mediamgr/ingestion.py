import face_recognition as fr
from hashlib import md5
from mediamgr import config
from mediamgr.models import *
import numpy as np
import os
from PIL import ExifTags, Image
import sys


def getFaceData (img: Image) -> list:
    # GPU memory safety guard rails
    max_edge = max(img.size)
    if max_edge > config.downsize_target:
        ratio = config.downsize_target / max_edge
        img = img.resize((int(round(img.size[0]*ratio)), int(round(img.size[1]*ratio))))
    
    # convert to what the face_recognition module wants
    img = np.array(img)

    face_locations = \
        fr.face_locations(img, 
                          number_of_times_to_upsample=config.upsample_times,
                          model=config.detection_model)
    
    return fr.face_encodings(   img, 
                                known_face_locations=face_locations,
                                num_jitters=config.encoding_jitters,
                                model=config.shape_predictor_model)


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
    if img.get_format_mimetype() != 'image/gif':
        metadata['xmp'] = img.getxmp()
    return img


def process_image_file (md: MediaDocument, dirname: str, filename: str):
    hash_md5 = md5()
    with open(os.path.join(dirname, filename), "rb") as f:
        for chunk in iter(lambda: f.read(256*1024), b""):
            hash_md5.update(chunk)
    
    hash = hash_md5.hexdigest()
    media = md.get(hash)
    if media is not None:
        print(f"{hash} - Already registered")
        return(None)

    md.new()
    md.setKey(hash)    
    metadata = {'hash_md5': hash}
    img = getPILMetaData(metadata, dirname, filename)
    md.merge(metadata)
    md.save()
    print(f"{hash} -- added media")
    if img.get_format_mimetype() == 'image/gif':
        print("Note: Facial detection in GIFs unsupported")
        return(None)
    
    return(img)


def main (argv: list=sys.argv):
    db = connect()
    md = MediaDocument(db)
    fd = FacesDocument(db)
    dirname = argv[1]
    for filename in os.listdir(dirname):
        print(f"filename: {filename}")

        img = process_image_file(md, dirname, filename)
        if img is None:
            continue

        face_encodings = getFaceData(img)

        for face in face_encodings:
            jface = json.dumps(list(face), indent=4)
            hash_md5 = md5(jface.encode('utf-8')).hexdigest()
            if fd.collection.has(hash_md5):
                # face collision: see issue #21 in geomat0101/mediamgr
                continue
            fd.new()
            fd.setKey(hash_md5)
            fd.document['face_identifier'] = list(face)
            fd.document['media_id'] = md._id
            fd.save()
            print(f"{hash_md5} -- added face -> {md._id}")
    sys.exit(0)