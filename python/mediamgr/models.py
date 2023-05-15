#!/bin/env python

import mediamgr.config as config
import arango
from arango.database import Database
import json

# adding collections to these lists will ensure they all
# exist at connect time or else they will be created
collections = "cast faces media".split()
edges = "appears_in face_matches_face".split()


def connect ():
    client = arango.ArangoClient(hosts=config.arango_url)
    db = client.db(
            config.arango_dbname, 
            username=config.arango_username, 
            password=config.arango_password)
    
    for c in collections:
        if not db.has_collection(c):
            db.create_collection(c)

    for e in edges:
        if not db.has_collection(e):
            db.create_collection(e, edge=True)

    return(db)


class CollectionDocument ():

    def __init__ (self, dbconn: Database, collection: str):
        self.dbconn = dbconn
        self.collection_name = collection
        self.collection = self.dbconn.collection(collection)
        self.document = None
        self.newDoc = None # is this a pre-existing doc
        self._id = ''
        self._key = ''
        self._rev = ''

        # these get set automatically, though the value of _id can
        # be influenced by setting the "_key" value
        # _id === {collection}/{_key}
        # "_rev" is just off limits
        self.prohibited_keys = ["_id", "_rev"]
        self.required_keys = []

    
    def __repr__ (self):
        return json.dumps(self.document, indent=4)


    def get (self, query):
        if str != type(query):
            raise ValueError("single string value searches only")
        self.newDoc = False
        self.setDocument(self.collection.get(query))


    def id_required (self):
        if not self._id:
            raise ValueError("No _id on current document.  Saved yet?")

    
    def new (self, document: dict = None):
        self.newDoc = True
        if document is None:
            self.template_init()
        else:
            self.setDocument(document)


    def save (self):
        if not self.validate():
            raise ValueError("Validation Failed!")
        
        if self.newDoc:
            metadata = self.collection.insert(self.document)
            self.newDoc = False
        else:
            metadata = self.collection.update(self.document)

        self._id = metadata['_id']
        self._key = metadata['_key']
        self._rev = metadata['_rev']

        return metadata


    def setDocument (self, document):
        if dict != type(document):
            raise ValueError("document must be a dict")
        
        if '_id' in document:
            self._id = document['_id']
        if '_key' in document:
            self._key = document['_key']
        if '_rev' in document:
            self._rev = document['_rev']

        self.document = document

    
    def setKey (self, key: str):
        if self.document is None:
            self.template_init()
        
        self.document['_key'] = key


    def template_init (self):
        self.document = {}
        for k in self.required_keys:
            self.document[k] = ''


    def validate (self):
        if not dict == type(self.document):
            raise ValueError("document must be a dict")
        
        for k in self.prohibited_keys:
            try:
                del self.document[k]
            except KeyError:
                pass

        for k in self.required_keys:
            if k not in self.document:
                raise ValueError("Missing required value for '{}'" % k)
        
        json.dumps(self.document) # test that it is serializable
        return(True)
    

class EdgeCollectionDocument (CollectionDocument):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys += ['_from', '_to']


class CastDocument (CollectionDocument):
    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'cast')
        self.required_keys += ["name", "refs"]

    def appears_in (self, media_id: str):
        self.id_required()

        ai = AppearsInDocument(self.dbconn)
        ai.new()
        ai.document['_from'] = self._id
        ai.document['_to'] = media_id
        ai.save()

    def template_init(self):
        super().template_init()
        self.document['refs'] = []

    def validate(self):
        if not super().validate():
            raise ValueError("Validation Failed!")

        if type([]) != type(self.document['refs']):
            raise ValueError('refs must be a list')
        
        return(True)


class FacesDocument (CollectionDocument):
    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'faces')
        self.required_keys += ['face_identifier', 'media_id', 'cast_id']
    
    def matches_face (self, face_id):
        self.id_required()

        fm = FaceMatchesFaceDocument(self.dbconn)
        fm.new()
        fm.document['_from'] = self._id
        fm.document['_to'] = face_id
        fm.save()


class MediaDocument (CollectionDocument):
    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'media')
        self.required_keys += ["metadata"]

    def template_init(self):
        super().template_init()
        self.document['metadata'] = {}

    def validate(self):
        if not super().validate():
            raise ValueError("Validation Failed!")

        if dict != type(self.document['metadata']):
            raise ValueError('metadata must be a dict')
        
        return(True)


class AppearsInDocument (EdgeCollectionDocument):
    def __init__(self, dbconn: Database):
        super().__init__(dbconn, 'appears_in')
        self.required_keys += ['first_seen', 'last_seen']


class FaceMatchesFaceDocument (EdgeCollectionDocument):
    def __init__(self, dbconn: Database):
        super().__init__(dbconn, 'face_matches_face')
        self.required_keys += ['confidence']

