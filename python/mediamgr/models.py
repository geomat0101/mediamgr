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
    # these get set automatically, though the value of _id can
    # be influenced by setting the "_key" value
    # _id === {collection}/{_key}
    # "_rev" is just off limits
    prohibited_keys = ["_id", "_rev"]
    required_keys = []

    def __init__ (self, dbconn: Database, collection: str):
        self.dbconn = dbconn
        self.collection_name = collection
        self.collection = self.dbconn.collection(collection)
        self.document = None
        self.newDoc = None # is this a pre-existing doc

    
    def __repr__ (self):
        return json.dumps(self.document, indent=4)


    def get (self, query):
        if str != type(query):
            raise ValueError("single string value searches only")
        self.newDoc = False

    
    def new (self, document: dict = None):
        self.newDoc = True
        if document is None:
            self.template_init()
        else:
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
    

    def save (self):
        if not self.validate():
            raise ValueError("Validation Failed!")
        
        if self.newDoc:
            metadata = self.collection.insert(self.document)
        else:
            metadata = self.collection.update(self.document)

        return metadata


class EdgeCollectionDocument (CollectionDocument):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys += ['_from', '_to']


class CastDocument (CollectionDocument):
    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'cast')
        self.required_keys += ["name", "refs"]

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

