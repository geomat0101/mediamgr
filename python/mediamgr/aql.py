from arango.database import Database

def execute_saved_query(db: Database, query_name: str, **kwargs):
    query = saved_queries[query_name]['query']
    bv = {}
    for v in saved_queries[query_name]['bind_vars']:
        if v not in kwargs:
            raise ValueError("missing required parameter: {}" % v)
        bv[v] = kwargs[v]

    return db.aql.execute(query, bind_vars=bv)


saved_queries = {
    'cast_by_media': {
        'query': '''
            FOR v
                IN 1..1
                INBOUND @media_id
                GRAPH "casting_graph"
                RETURN v
        ''',
        'bind_vars': ['media_id']
    },
    'media_by_cast': {
        'query': '''
            FOR v
                IN 1..1
                OUTBOUND @cast_id
                GRAPH "casting_graph"
                RETURN v
        ''',
        'bind_vars': ['cast_id']
    },
    'faces_matching_face': {
        'query': '''
            FOR v
                IN 1..1
                ANY @face_id
                GRAPH "matching_faces"
                RETURN v
        ''',
        'bind_vars': ['face_id']
    }
}
