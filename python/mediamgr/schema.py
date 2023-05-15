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
        'required': ['_from', '_to', 'first_seen', 'last_seen']
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
        'required': ['_from', '_to', 'confidence']
    },
    'level': 'moderate',
    'message': 'Schema Validation Failed.'
}