import sqlite3
import core


def add_project(db, cursor: sqlite3.Cursor, name: str, priority: int):
    cursor.execute("INSERT INTO projects(name, priority) VALUES (?, ?)", (name, priority))
    db.commit()


def list_projects(cursor: sqlite3.Cursor, open_projects: bool = None):
    if open_projects is None:
        query = "SELECT id, name, priority, 0 FROM projects ORDER BY priority DESC"
    else:
        query = "SELECT projects.id, projects.name, projects.priority, sum(tasks.weight) FROM projects " \
                "INNER JOIN tasks ON tasks.project = projects.id " \
                "WHERE open=%d GROUP BY tasks.project ORDER BY projects.priority DESC" \
                % (int(open_projects))
    cursor.execute(query)
    projects = cursor.fetchall()
    return [{
        "id": p[0],
        "name": p[1],
        "priority": p[2],
        "total": p[3]
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


def get_project_progress(cursor: sqlite3.Cursor, id_: int):
    cursor.execute("SELECT SUM(weight) FROM tasks WHERE project=?", (id_,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(weight) FROM tasks WHERE project=? AND status = 0", (id_,))
    closed = cursor.fetchone()[0]
    return total, closed
