#!/usr/bin/env python3
"""
Common, interface independent functions.

Implement most of the Aide functionality.
"""
import datetime
import logging
import json
import os
import re
import sqlite3

import matplotlib.pyplot as plt
import rpg_mod

def add_task(db, cursor: sqlite3.Cursor, name, priority, time, date, weight, repeat, project: int = None):
    if time:
        priority += 100

    if date:
        date = relative_date_to_sql_query(date)
    else:
        date = "date('now')"

    repeat = "+" + repeat if repeat else None

    cursor.execute("INSERT INTO tasks(name, priority, due_time, due_date, weight, repeat_period, project) VALUES "
                   "(?, ?, " + local_to_utc("?") + "," + date + ", ?, ?, ?)",
                   (name, priority, time, weight, repeat, project))
    db.commit()


def list_tasks(cursor: sqlite3.Cursor, only_top_result: bool = False, exclude_closed_tasks: bool = True,
               due_date: str = None, project: int = None, list_overdue_tasks: bool = False):
    query = "SELECT id, name, priority, " + utc_to_local("due_time") + ", status, weight, due_date, project " \
                                                                       "FROM tasks WHERE "
    where_clauses = []
    query_arguments = []

    # parametrize the query
    if only_top_result:
        query += "status=1 AND" \
                 " (due_time < current_time OR due_time IS NULL) AND due_date = current_date " \
                 " ORDER BY priority DESC " \
                 " LIMIT 1"
    else:
        if exclude_closed_tasks:
            where_clauses.append("status=1")

        if project:
            where_clauses.append("project=" + str(project))

        if due_date:
            due_date = relative_date_to_sql_query(due_date)
            if due_date == "null":
                where_clauses.append("due_date is null")
            elif list_overdue_tasks:
                where_clauses.append("due_date<" + due_date)
            else:
                where_clauses.append("due_date=" + due_date)
        else:
            if list_overdue_tasks:
                where_clauses.append("due_date < current_date")
            else:
                where_clauses.append("due_date = current_date")

        query += " AND ".join(where_clauses)
        query += " ORDER BY priority DESC"

    # run the query and repack into a list of dictionaries
    cursor.execute(query, query_arguments)
    tasks = cursor.fetchall()
    return [{
        "id": t[0],
        "name": t[1],
        "priority": t[2],
        "due_time": t[3],
        "status": t[4],
        "weight": t[5],
        "due_date": t[6],
        "project": t[7]
    } for t in tasks]


def modify_task(db, cursor: sqlite3.Cursor, id_: str, name: str = "", priority: int = -1, time: str = "",
                weight: float = -1, repeat: str = "", due_date: str = "", status: int = -1, project: int = None):
    setters = []
    query_arguments = []

    if name:
        setters.append("name=?")
        query_arguments.append(name)

    if priority >= 0:
        setters.append("priority=?")
        query_arguments.append(priority)

    if time:
        setters.append("due_time=" + local_to_utc("?"))
        query_arguments.append(time)

    if weight >= 0:
        setters.append("weight=?")
        query_arguments.append(weight)

    if repeat:
        setters.append("repeat_period=?")
        query_arguments.append("+" + repeat)

    if due_date:
        due_date = relative_date_to_sql_query(due_date)
        setters.append("due_date=" + due_date)

    if status == 0 or status == 1:
        setters.append("status=?")
        query_arguments.append(status)

    if project:
        setters.append("project=?")
        query_arguments.append(project)

    query = "UPDATE tasks SET " + " AND ".join(setters) + " WHERE id = ?"
    query_arguments.append(id_)

    cursor.execute(query, query_arguments)
    db.commit()


def close_task(db, cursor: sqlite3.Cursor, id_: str):
    cursor.execute("SELECT name, quest FROM tasks WHERE id = ?", (id_,))
    name, quest = cursor.fetchone()

    cursor.execute("UPDATE tasks SET status=0 WHERE id = ?", (id_,))
    db.commit()

    if quest:
        rpg_mod.close_quest(db, cursor, quest)

    return name


def delete_task(db, cursor: sqlite3.Cursor, id_: str):
    cursor.execute("DELETE FROM tasks WHERE id = ?", (id_,))
    db.commit()


def add_note(db, cursor: sqlite3.Cursor, date: str, text: str):
    if date:
        cursor.execute("INSERT INTO notes(date, text) VALUES (?, ?)", (date, text))
    else:
        cursor.execute("INSERT INTO notes(date, text) VALUES (date('now'), ?)", (text,))
    db.commit()


def productivity_plot(cursor: sqlite3.Cursor):
    cursor.execute('SELECT sum(weight),due_date FROM tasks WHERE status=0 GROUP BY due_date')
    data = cursor.fetchall()

    if len(data) <= 2:
        logging.error("Not enough data to build a plot")
        return

    date_start = datetime.datetime.strptime(data[0][1], "%Y-%m-%d")
    date_end = datetime.datetime.strptime(data[-1][1], "%Y-%m-%d")
    dates = [(date_start + datetime.timedelta(days=x)).strftime("%Y-%m-%d") for x in
             range(0, (date_end - date_start).days + 1)]

    weights = []
    i = 0
    for row in data:
        while row[1] != dates[i]:
            weights.append(0.0)
            i += 1

        weights.append(row[0])
        i += 1

    fig = plt.figure(figsize=(10, 1))
    ax = fig.add_subplot(111)
    ax.bar(dates, weights)
    ax.yaxis.grid(True, linestyle=':', which='major')
    labels = ax.set_xticklabels(dates)
    plt.setp(labels, rotation=90)
    ax.set_aspect(3.)
    plt.show()

    return


def get_total_weight(cursor: sqlite3.Cursor, closed=False):
    if closed:
        query = "SELECT sum(weight) FROM tasks WHERE due_date=current_date AND status=0 GROUP BY due_date"
    else:
        query = "SELECT sum(weight) FROM tasks WHERE due_date=current_date GROUP BY due_date"
    query_arguments = []

    result = cursor.execute(query, query_arguments).fetchone()
    return result[0] if result else 0.0


def relative_date_to_sql_query(date: str):
    if date[0] == "+":
        return "date('now', '" + date + "')"

    if date == "today":
        return "date('now')"

    if date == "tomorrow":
        return "date('now', '+1 day')"

    if date == "no":
        return "null"

    return "date('" + date + "')"


# SQLite doesn't handle daylight saving properly
# The following 2 functions bypass this limitation
def utc_to_local(time: str):
    return "strftime('%H:%M', " \
           "    strftime('%s', " + time + ") + strftime('%s', 'now', 'localtime') - strftime('%s', 'now'), 'unixepoch')"


def local_to_utc(time: str):
    return "strftime('%H:%M', " \
           "    strftime('%s', " + time + ") + strftime('%s', 'now') - strftime('%s', 'now', 'localtime'), 'unixepoch')"


def read_configuration():
    with open(os.path.expanduser("~/.aide.conf")) as f:
        config = json.load(f)
    return config


def validate_date(date_string: str) -> bool:
    if not date_string:
        return True

    pattern = r"\d{4}-(0[1-9]|1[012])-([0-2]\d|3[0-1])"
    result = re.search(pattern, date_string)
    return bool(result)


def validate_relative_date(date_string: str) -> bool:
    if not date_string:
        return True

    pattern = r"\d{4}-(0[1-9]|1[012])-([0-2]\d|3[0-1])|\+\d{1,3} (days|months|years)|today|tomorrow|no"
    result = re.search(pattern, date_string)
    return bool(result)


def validate_time(time_string: str) -> bool:
    if not time_string:
        return True

    try:
        datetime.datetime.strptime(time_string, "%H:%M")
    except ValueError:
        return False
    return True


def validate_time_period(date_string: str) -> bool:
    if not date_string:
        return True

    pattern = r"\d{1,3} (days|months|years)|workdays"
    result = re.search(pattern, date_string)
    return bool(result)
