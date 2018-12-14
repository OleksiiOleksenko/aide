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
import psutil

import matplotlib.pyplot as plt
import pandas
import rpg_mod


def add_task(db, cursor: sqlite3.Cursor, name, priority, time, date, weight, repeat=None, project=None, quest=None):
    if time:
        priority += 100

    if date:
        date = relative_date_to_sql_query(date)
    else:
        date = "date('now')"

    if project is None:
        project = 1

    cursor.execute("INSERT INTO tasks(name, priority, due_time, due_date, weight, repeat_period, project, quest) VALUES"
                   " (?, ?, " + local_to_utc("?") + "," + date + ", ?, ?, ?, ?)",
                   (name, priority, time, weight, repeat, project, quest))
    db.commit()


def list_tasks(cursor: sqlite3.Cursor, only_top_result: bool = False, exclude_closed_tasks: bool = True,
               exclude_overdue_tasks: bool = False, due_date: str = None, project: int = None):
    query = "SELECT id, name, priority, " + utc_to_local("due_time") + ", status, weight, due_date, " \
                                                                       "project, priority_in_project " \
                                                                       "FROM tasks WHERE "
    where_clauses = []
    query_arguments = []

    # parametrize the query
    if only_top_result:
        query += "status=1 AND" \
                 " (due_time < current_time OR due_time IS NULL) AND due_date <= current_date " \
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
            elif exclude_overdue_tasks:
                where_clauses.append("due_date=" + due_date)
            else:
                where_clauses.append("due_date<=" + due_date)

        query += " AND ".join(where_clauses)
        if project:
            query += " ORDER BY priority_in_project "
        else:
            query += " ORDER BY priority "
        query += "DESC LIMIT 35"

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
        "project": t[7],
        "priority_in_project": t[8]
    } for t in tasks]


def modify_task(db, cursor: sqlite3.Cursor, id_: str, name: str = "", priority: int = -1, time: str = "",
                weight: float = -1, repeat: str = "", due_date: str = "", status: int = -1, project: int = None,
                priority_in_project: int = -1):
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

    if priority_in_project >= 0:
        setters.append("priority_in_project=?")
        query_arguments.append(priority_in_project)

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

    # for i3 integration
    os.system('pkill -SIGRTMIN+10 i3blocks')

    return name


def delete_task(db, cursor: sqlite3.Cursor, id_: str):
    cursor.execute("DELETE FROM tasks WHERE id = ?", (id_,))
    db.commit()


def add_note(db, cursor: sqlite3.Cursor, date: str, text: str):
    date = relative_date_to_sql_query(date)

    if date:
        cursor.execute("INSERT INTO notes(date, text) VALUES (" + date + ",?)", (text,))
    else:
        cursor.execute("INSERT INTO notes(date, text) VALUES (date('now'), ?)", (text,))
    db.commit()


def productivity_plot(cursor: sqlite3.Cursor, project_ids: list = None, interval: str = None):
    if not project_ids or project_ids == [None]:
        cursor.execute('SELECT sum(tasks.weight),tasks.due_date, projects.name FROM tasks '
                       'INNER JOIN projects ON tasks.project = projects.id '
                       'WHERE status=0 AND due_date is not NULL GROUP BY due_date,project'
                       )
    else:
        cursor.execute('SELECT sum(tasks.weight),tasks.due_date, projects.name FROM tasks '
                       'INNER JOIN projects ON tasks.project = projects.id '
                       'WHERE status=0 AND due_date is not NULL AND project IN ({})'
                       'GROUP BY due_date,project'.format(','.join(['?'] * len(project_ids))),
                       project_ids
                       )
    data = cursor.fetchall()

    if len(data) <= 2:
        return False

    # import into a DataFrame
    labels = ["weight", "date", "project"]
    df = pandas.DataFrame.from_records(data, columns=labels)
    df = df.pivot(index="date", columns="project", values="weight")

    # fill the missing dates
    dates = pandas.date_range(data[0][1], data[-1][1])
    df.index = pandas.DatetimeIndex(df.index)
    df = df.reindex(dates, fill_value=0)
    if interval:
        df = df.resample(interval).sum()

    # build the plot
    fig = plt.figure(figsize=(12, 1))
    ax = fig.add_subplot(111)
    plot = df.plot(
        ax=ax,
        kind="bar",
        stacked=True,

    )
    ax.legend(loc='upper left')

    ax.yaxis.grid(True, linestyle=':', which='major')
    labels = ax.set_xticklabels([pandas_datetime.strftime("%Y-%m-%d") for pandas_datetime in df.index])
    plt.setp(labels, rotation=90)
    plt.show()

    return True


def get_total_weight(cursor: sqlite3.Cursor, closed=False, week_total=False):
    if closed:
        query = "SELECT sum(weight) FROM tasks WHERE due_date=current_date AND status=0 GROUP BY due_date"
    elif week_total:
        query = "SELECT sum(weight) FROM tasks WHERE date(due_date) >= date('now', 'weekday 1', '-7 days') AND status=0"
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
