import mediamgr.config
from mediamgr.models import *
from mediamgr.schema import schema
from jsonschema.validators import validate as json_validate
import pytest


def test_e2e():
    # happy path speed run -- destructive to target db
    mediamgr.config.arango_dbname = 'mediamgr-pytest'

    db = connect()

    # tear it down...
    user_collections =  [ _['name'] for _ in db.collections() if not _['system'] ]

    for c in user_collections:
        db.delete_collection(c)
    
    for g in [ _['name'] for _ in db.graphs() ]:
        db.delete_graph(g)

    # ... to build it back up again
    db = None
    db = connect()


    # use a CastDocument to exercise the base CollectionDocument class
    cache = {}

    ## __init__; transitively: new, setDocument, validate
    c = CastDocument(db)
    assert c.collection_name == 'cast'
    assert c._id == c._key == c._rev == ''
    json_validate(c.document, schema['cast']['schema']['rule'])

    ## setKey
    c.setKey('1000')
    assert c.document['_key'] == '1000'

    ## save (new insert)
    c.save()
    ## save (update existing)
    c.document['name'] = 'foo'
    c.save()

    cache['cast/1000'] = repr(c)

    ## get
    c = None
    c = CastDocument(db)
    c.get('1000')
    assert repr(c) == cache['cast/1000']

    ## id_required
    c.new()
    with pytest.raises(ValueError):
        c.id_required()
    c.validate()

    # end of CollectionDocument tests

    
    # seed remaining test data
    c.new()
    c.setKey('1010')
    c.save()
    cache['cast/1010'] = repr(c)

    m = MediaDocument(db)
    m.setKey('2000')
    m.save()
    cache['media/2000'] = repr(m)
    m.new()
    m.setKey('2010')
    m.save()
    cache['media/2010'] = repr(m)
    m.new()
    m.setKey('2020')
    m.save()
    cache['media/2020'] = repr(m)

    f = FacesDocument(db)
    f.setKey('3000')
    f.document['cast_id'] = 'cast/1000'
    f.document['media_id'] = 'media/2000'
    f.save()
    cache['faces/3000'] = repr(f)
    f.new()
    f.setKey('3010')
    f.document['cast_id'] = 'cast/1000'
    f.document['media_id'] = 'media/2010'
    f.save()
    cache['faces/3010'] = repr(f)
    f.new()
    f.setKey('3020')
    f.document['cast_id'] = 'cast/1010'
    f.document['media_id'] = 'media/2010'
    f.save()
    cache['faces/3020'] = repr(f)
    f.new()
    f.setKey('3030')
    f.document['cast_id'] = 'cast/1010'
    f.document['media_id'] = 'media/2020'
    f.save()
    cache['faces/3030'] = repr(f)


    # CastDocument class specific tests

    ## appears_in, get_media
    c.get('1000')
    c.appears_in('media/2000')
    c.appears_in('media/2010')
    media = sorted([ _['_key'] for _ in c.get_media() ])
    assert len(media) == 2
    assert media[0] == '2000'
    assert media[1] == '2010'
    c.get('1010')
    c.appears_in('media/2010')
    c.appears_in('media/2020')
    media = sorted([ _['_key'] for _ in c.get_media() ])
    assert len(media) == 2
    assert media[0] == '2010'
    assert media[1] == '2020'

    ## get_faces
    c.get('1000')
    faces = sorted([ _['_key'] for _ in c.get_faces() ])
    assert len(faces) == 2
    assert faces[0] == '3000'
    assert faces[1] == '3010'
    c.get('1010')
    faces = sorted([ _['_key'] for _ in c.get_faces() ])
    assert len(faces) == 2
    assert faces[0] == '3020'
    assert faces[1] == '3030'


    # FaceDocument class

    ## matches_face, get_matching_faces
    f.get('3000')
    f.matches_face('faces/3010')
    faces = sorted([ _['_key'] for _ in f.get_matching_faces() ])
    assert len(faces) == 1
    assert faces[0] == '3010'
    f.get('3010')
    faces = sorted([ _['_key'] for _ in f.get_matching_faces() ])
    assert len(faces) == 1
    assert faces[0] == '3000'
    f.get('3020')
    f.matches_face('faces/3030')
    faces = sorted([ _['_key'] for _ in f.get_matching_faces() ])
    assert len(faces) == 1
    assert faces[0] == '3030'
    f.get('3030')
    faces = sorted([ _['_key'] for _ in f.get_matching_faces() ])
    assert len(faces) == 1
    assert faces[0] == '3020'


    # MediaDocument class

    ## get_cast
    m.get('2000')
    cast = sorted([ _['_key'] for _ in m.get_cast() ])
    assert len(cast) == 1
    assert cast[0] == '1000'
    m.get('2010')
    cast = sorted([ _['_key'] for _ in m.get_cast() ])
    assert len(cast) == 2
    assert cast[0] == '1000'
    assert cast[1] == '1010'
    m.get('2020')
    cast = sorted([ _['_key'] for _ in m.get_cast() ])
    assert len(cast) == 1
    assert cast[0] == '1010'

    ## get_faces
    m.get('2000')
    faces = sorted([ _['_key'] for _ in m.get_faces() ])
    assert len(faces) == 1
    assert faces[0] == '3000'
    m.get('2010')
    faces = sorted([ _['_key'] for _ in m.get_faces() ])
    assert len(faces) == 2
    assert faces[0] == '3010'
    assert faces[1] == '3020'
    m.get('2020')
    faces = sorted([ _['_key'] for _ in m.get_faces() ])
    assert len(faces) == 1
    assert faces[0] == '3030'
