import sqlite3
import core


def add_project(db, cursor: sqlite3.Cursor, name: str, priority: int):
    cursor.execute("INSERT INTO projects(name, priority) VALUES (?, ?)", (name, priority))
    db.commit()


def list_projects(cursor: sqlite3.Cursor):
    query = "SELECT id, name, priority FROM projects"
    cursor.execute(query)
    projects = cursor.fetchall()
    return [{
        "id": p[0],
        "name": p[1],
        "priority": p[2],
    } for p in projects]


def modify_project(db, cursor: sqlite3.Cursor, id_: str, name: str = None, priority: int = None):
    setters = []
    query_arguments = []

    if name is not None:
        setters.append("name=?")
        query_arguments.append(name)

    if priority is not None:
        setters.append("priority=?")
        query_arguments.append(priority)

    query = "UPDATE projects SET " + " AND ".join(setters) + " WHERE id = ?"
    query_arguments.append(id_)

    cursor.execute(query, query_arguments)
    db.commit()
