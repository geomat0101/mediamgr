from arango.cursor import Cursor
from arango.database import Database
from arango.result import Result

def execute_saved_query(db: Database, query_name: str, **kwargs) -> Result[Cursor]:
    """Execute a saved query and return the cursor

    db          --  arango.database.Database instance
    query_name  --  key in saved_queries dict
    **kwargs    --  k/v params mapping to the query's bind_var requirements
                    see query definition for variable names

    Example:
        execute_saved_query(db, 'myQuery', barOne='foo', bazTwo='bar'[, ...])
    """
    query = saved_queries[query_name]['query']
    bv = {}
    for v in saved_queries[query_name]['bind_vars']:
        if v not in kwargs:
            raise ValueError("missing required parameter: '{}'" % v)
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
