#!/bin/env python

import mediamgr.aql as aql
import mediamgr.config as config
from mediamgr.schema import collections, graphs, indexes, schema
import arango
from arango.cursor import Cursor
from arango.database import Database
from arango.result import Result
import json
from jsonschema.validators import validate as json_validate


def connect () -> Database:
    """Connect to ArangoDB

    uses connection settings in mediamgr.config
    """
    client = arango.ArangoClient(hosts=config.arango_url)
    db = client.db(
            config.arango_dbname, 
            username=config.arango_username, 
            password=config.arango_password)

    # check for missing collections and create if needed
    for c in schema.keys():
        if not db.has_collection(c):
            if c in collections['edge']:
                db.create_collection(c, edge=True, schema=schema[c])
            else:
                db.create_collection(c, schema=schema[c])

            if c in indexes:
                # this is only safe because we just created the collection
                # schema updates need to check if an index exists first
                for field in indexes[c]:
                    db.collection(c).add_persistent_index(fields=[field])

    # check for missing graphs and create if needed
    for g, v in graphs.items():
        if not db.has_graph(g):
            graph = db.create_graph(g)
            graph.create_edge_definition(
                edge_collection=v['edge_collection'],
                from_vertex_collections=v['from_vertex_collections'],
                to_vertex_collections=v['to_vertex_collections']
            )

    return(db)


class CollectionDocument ():
    """Base class for managing documents within a named ArangoDB collection

    This defines the base methods which are then extended by classes that 
    implement interfaces for interacting with objects backed by specific
    db collections.
    """

    def __init__ (self, dbconn: Database, collection: str):
        """Instantiate a collection object

        dbconn      --  db handle from mediamgr.connect()
        collection  --  name of collection to load
        """
        self.dbconn = dbconn
        self.collection_name = collection
        self.collection = self.dbconn.collection(collection)

        self.document = None    # The Document - use setDocument to load an entire top-level doc.
                                #   Manipulating individual property values directly is fine
                                #   as long as they don't violate the collection's schema

        self._id = ''           # {collection}/{_key} -- arangodb managed at save
        self._key = ''          # can be user-specified via setKey()
        self._rev = ''          # arangoDB internal document versioning

        self.prohibited_keys = ["_id", "_rev"]  # arangodb managed, filtered just prior to save

    
    def __repr__ (self):
        return json.dumps(self.document, indent=4)


    def get (self, query: str):
        """Get a record from a collection

        query   --  Document ID or key
        """
        if str != type(query):
            raise ValueError("need str: _id or _key value")
        self.setDocument(self.collection.get(query))


    def id_required (self):
        """Verifies the _id property is set"""
        if not self._id:
            raise ValueError("No _id on current document.  Saved yet?")

    
    def new (self, document: dict = None):
        """Create a new collection document

        document    --  optional user-supplied dictionary conforming to the collection schema
                        None will populate the document with an empty template
        """
        if document is None:
            self.template_init()
        else:
            self.setDocument(document)


    def save (self) -> dict:
        """Save the collection document
        
        Validates and saves the document to the ArangoDB collection
        Returns the metadata from the server after the insert/update
        """
        if not self.validate():
            raise ValueError("Validation Failed!")
        
        for k in self.prohibited_keys:
            try:
                del self.document[k]
            except KeyError:
                pass

        if '_rev' in self.document:
            metadata = self.collection.update(self.document)
        else:
            metadata = self.collection.insert(self.document)

        self._id = self.document['_id'] = metadata['_id']
        self._key = self.document['_key'] = metadata['_key']
        self._rev = self.document['_rev'] = metadata['_rev']

        return metadata


    def setDocument (self, document: dict):
        """setter method for the collection document
        
        document    --  dict conforming to the collection's schema
        """
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
        """setter method for the document's _key property"""
        if self.document is None:
            self.template_init()
        
        self.document['_key'] = key


    def template_init (self):
        """Generate a new document using a template based on the collection's schema"""
        doc = {}
        for k,v in schema[self.collection_name]['rule']['properties'].items():
            vtype = v['type'].lower()
            if vtype == 'null':
                doc[k] = None
            elif vtype == 'boolean':
                doc[k] = False
            elif vtype == 'object':
                doc[k] = {}
            elif vtype == 'array':
                doc[k] = []
            elif vtype == 'number':
                doc[k] = 0.0
            elif vtype == 'string':
                doc[k] = ''
            elif vtype == 'integer':
                doc[k] = 0
            else:
                raise ValueError("illegal type value '{}' in jsonschema for collection '{}'" % vtype, self.collection_name)
        
        if '_rev' in doc:
            # this is a new document, and having _rev in there will make save try to update it 
            # instead of insert it.  This means somebody put _rev into the collection schema 
            # and should not have.
            del doc['_rev']

        self.setDocument(doc)
        

    def validate (self, document: dict = None):
        """Validate against the collection's jsonschema definition
        
        document    --  documents other than the current object's may be submitted for validation
                        None will validate the current object's document by default
        """
        if document is None:
            document = self.document

        if not dict == type(document):
            raise ValueError("document must be a dict")
        
        json_validate(document, schema[self.collection_name]['rule'])
        return(True)
    

class CastDocument (CollectionDocument):
    """Derived class for documents in the 'cast' collection"""

    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'cast')

    def appears_in (self, media_id: str) -> dict:
        """Create an 'appears_in' edge from this document to a media document

        media_id    --  Id of the target 'media' collection document
        """
        self.id_required()
        ai = AppearsInDocument(self.dbconn)
        ai.new()
        ai.document['_from'] = self._id
        ai.document['_to'] = media_id
        return ai.save()
    
    def get_faces (self) -> Result[Cursor]:
        """Get faces linked to this document
        
        Returns an iterable cursor with 'faces' collection documents
        """
        self.id_required()
        f = FacesDocument(self.dbconn)
        return f.collection.find({'cast_id': self._id})
    
    def get_media (self) -> Result[Cursor]:
        """Get media linked to this document
        
        Returns an iterable cursor with 'media' collection documents
        """
        self.id_required()
        return aql.execute_saved_query(self.dbconn, 
                                       'media_by_cast', 
                                       cast_id=self._id)


class FacesDocument (CollectionDocument):
    """Derived class for documents in the 'faces' collection"""

    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'faces')
    
    def get_matching_faces (self) -> Result[Cursor]:
        """Get faces linked to this document
        
        Returns an iterable cursor with 'faces' collection documents
        """
        self.id_required()
        return aql.execute_saved_query(self.dbconn,
                                       'faces_matching_face',
                                       face_id=self._id)

    def matches_face (self, face_id) -> dict:
        """Create a 'face_matches_face' edge from this document to another face document

        face_id    --  Id of the target 'faces' collection document
        """
        self.id_required()
        fm = FaceMatchesFaceDocument(self.dbconn)
        fm.new()
        fm.document['_from'] = self._id
        fm.document['_to'] = face_id
        return fm.save()


class MediaDocument (CollectionDocument):
    """Derived class for documents in the 'media' collection"""

    def __init__ (self, dbconn: Database):
        super().__init__(dbconn, 'media')

    
    def get_cast (self) -> Result[Cursor]:
        """Get cast linked to this document
        
        Returns an iterable cursor with 'cast' collection documents
        """
        self.id_required()
        return aql.execute_saved_query(self.dbconn,
                                       'cast_by_media',
                                       media_id=self._id)

    
    def get_faces (self) -> Result[Cursor]:
        """Get faces linked to this document
        
        Returns an iterable cursor with 'faces' collection documents
        """
        self.id_required()
        f = FacesDocument(self.dbconn)
        return f.collection.find({'media_id': self._id})


class AppearsInDocument (CollectionDocument):
    """Derived class for documents in the 'appears_in' edge collection"""

    def __init__(self, dbconn: Database):
        super().__init__(dbconn, 'appears_in')


class FaceMatchesFaceDocument (CollectionDocument):
    """Derived class for documents in the 'face_matches_face' edge collection"""

    def __init__(self, dbconn: Database):
        super().__init__(dbconn, 'face_matches_face')

