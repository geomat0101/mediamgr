#!/bin/env python

import mediamgr.config as config
from mediamgr.schema import edge_collections, indexes, schema
import arango
from arango.database import Database
import json
from jsonschema.validators import validate as json_validate


def connect ():
    client = arango.ArangoClient(hosts=config.arango_url)
    db = client.db(
            config.arango_dbname, 
            username=config.arango_username, 
            password=config.arango_password)

    for c in schema.keys():
        if not db.has_collection(c):
            if c in edge_collections:
                # FIXME: schemas don't validate in arango with edge collections.
                # local jsonschema passes, looks like an arango bug

                # db.create_collection(c, edge=True, schema=schema[c])
                db.create_collection(c, edge=True)
            else:
                db.create_collection(c, schema=schema[c])

            if c in indexes:
                for field in indexes[c]:
                    db.collection(c).add_persistent_index(fields=[field])

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
        
        for k in self.prohibited_keys:
            try:
                del self.document[k]
            except KeyError:
                pass

        if self.newDoc:
            metadata = self.collection.insert(self.document)
            self.newDoc = False
        else:
            metadata = self.collection.update(self.document)

        self._id = self.document['_id'] = metadata['_id']
        self._key = self.document['_key'] = metadata['_key']
        self._rev = self.document['_rev'] = metadata['_rev']

        return metadata


    def setDocument (self, document):
        if dict != type(document):
            raise ValueError("document must be a dict")
        
        self._id = self._key = self._rev = ''
        if '_id' in document:
            self._id = document['_id']
        if '_key' in document:
            self._key = document['_key']
        if '_rev' in document:
            self._rev = document['_rev']

        self.validate(document=document)
        self.document = document

    
    def setKey (self, key: str):
        if self.document is None:
            self.template_init()
        
        self.document['_key'] = key


    def template_init (self):
        newDoc = {}
        for k,v in schema[self.collection_name]['rule']['properties'].items():
            vtype = v['type'].lower()
            if vtype == 'null':
                newDoc[k] = None
            elif vtype == 'boolean':
                newDoc[k] = False
            elif vtype == 'object':
                newDoc[k] = {}
            elif vtype == 'array':
                newDoc[k] = []
            elif vtype == 'number':
                newDoc[k] = 0.0
            elif vtype == 'string':
                newDoc[k] = ''
            elif vtype == 'integer':
                newDoc[k] = 0
            else:
                raise ValueError("illegal type value '{}' in jsonschema for collection '{}'" % vtype, self.collection_name)
        
        self.setDocument(newDoc)
        

    def validate (self, document=None):
        if document is None:
            document = self.document

        if not dict == type(document):
            raise ValueError("document must be a dict")
        
        json_validate(document, schema[self.collection_name]['rule'])
        return(True)
    

class CastDocument (CollectionDocument):
    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'cast')

    def appears_in (self, media_id: str):
        self.id_required()

        ai = AppearsInDocument(self.dbconn)
        ai.new()
        ai.document['_from'] = self._id
        ai.document['_to'] = media_id
        return ai.save()
    
    def get_faces (self):
        self.id_required()

        f = FacesDocument(self.dbconn)
        return f.collection.find({'cast_id': self._id})
    
    def get_media (self):
        self.id_required()

        m = MediaDocument(self.dbconn)
        raise NotImplementedError("needs a graph traversal")


class FacesDocument (CollectionDocument):
    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'faces')
    
    def matches_face (self, face_id):
        self.id_required()

        fm = FaceMatchesFaceDocument(self.dbconn)
        fm.new()
        fm.document['_from'] = self._id
        fm.document['_to'] = face_id
        return fm.save()


class MediaDocument (CollectionDocument):
    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'media')
    
    def get_faces (self):
        self.id_required()

        f = FacesDocument(self.dbconn)
        return f.collection.find({'media_id': self._id})


class AppearsInDocument (CollectionDocument):
    def __init__(self, dbconn: Database):
        super().__init__(dbconn, 'appears_in')


class FaceMatchesFaceDocument (CollectionDocument):
    def __init__(self, dbconn: Database):
        super().__init__(dbconn, 'face_matches_face')

