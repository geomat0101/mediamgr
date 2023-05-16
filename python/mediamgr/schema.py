
# collections not listed here default to 'standard' collections
collections = {
    'edge': ['appears_in', 'face_matches_face'],
    'vertex': ['cast', 'faces', 'media']
}


# these are created after the collections
graphs = {
    'casting_graph': {
        'edge_collection': 'appears_in',
        'from_vertex_collections': ['cast'],
        'to_vertex_collections': ['media']
    },
    'matching_faces': {
        'edge_collection': 'face_matches_face',
        'from_vertex_collections': ['faces'],
        'to_vertex_collections': ['faces']
    }
}


# these create separate persistent indexes for each property in the list
indexes = {
    'faces': ['cast_id', 'media_id']
}


# collection schemas
# keys are the collection names

# rule, level, and message are arangodb specific

# the rule value conforms to the jsonschema standard
# https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-any

# the top level of the schema for these will always be type: object

# do NOT put the _from or _to properties in the required list for edge collections
#   arango will fail validation on these even though jsonschema will pass them

# do NOT put the _id, _key, _rev, or _oldrev properties in the schema anywhere
#   especially _rev, as the existence (or not) decides whether we try to insert or update on save

schema = {}

schema['cast'] = {
    'rule': {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'refs': {'type': 'array'}
        },
        'required': ['name', 'refs']
    },
    'level': 'moderate',
    'message': 'Schema Validation Failed.'
}

schema['faces'] = {
    'rule': {
        'type': 'object',
        'properties': {
            'face_identifier':  {'type': 'string'},
            'media_id':         {'type': 'string'},
            'cast_id':          {'type': 'string'}
        },
        'required': ['face_identifier', 'media_id', 'cast_id']
    },
    'level': 'moderate',
    'message': 'Schema Validation Failed.'
}

schema['media'] = {
    'rule': {
        'type': 'object',
        'properties': {
            'metadata': {'type': 'object'}
        },
        'required': ['metadata']
    },
    'level': 'moderate',
    'message': 'Schema Validation Failed.'
}

schema['appears_in'] = {
    'rule': {
        'type': 'object',
        'properties': {
            '_from':        {'type': 'string'},
            '_to':          {'type': 'string'},
            'first_seen':   {'type': 'string'},
            'last_seen':    {'type': 'string'}
        },
        'required': ['first_seen', 'last_seen']
    },
    'level': 'moderate',
    'message': 'Schema Validation Failed.'
}

schema['face_matches_face'] = {
    'rule': {
        'type': 'object',
        'properties': {
            '_from':        {'type': 'string'},
            '_to':          {'type': 'string'},
            'confidence':   {'type': 'string'}
        },
        'required': ['confidence']
    },
    'level': 'moderate',
    'message': 'Schema Validation Failed.'
}
