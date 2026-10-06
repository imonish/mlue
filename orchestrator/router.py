def route_query(state):

    query = state["user_query"].lower()

    # Phase 1:
    # We are building/testing the SQL workflow first.
    return {
        "route": "sql"
    }