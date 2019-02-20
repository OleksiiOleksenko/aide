#!/usr/bin/env python3
"""
Command-line interface to Aide
"""

import datetime
import logging
import re
import sqlite3
from argparse import ArgumentParser, ArgumentTypeError

import core
import rpg_mod


def get_arguments():
    """
    Parse command line arguments
    :return Namespace: parsed arguments
    """
    parser = ArgumentParser(description='')
    subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_name')

    parser.add_argument(
        '-v', '--verbose',
        type=int,
        default=1,
        help='Verbosity level: [under construction]'
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        required=False,
        help='Debug mode [under construction]'
    )

    # adding tasks
    parser_add = subparsers.add_parser('add', help='Create a new task')
    parser_add.add_argument(
        'name',
        type=str,
        help="Name of the task to add"
    )
    parser_add.add_argument(
        '-p', '--priority',
        type=int,
        default=0,
        help="Priority of the task"
    )
    parser_add.add_argument(
        '-t', '--time',
        type=validate_time,
        help="Start time of the task. Format: -t HH:MM"
    )
    parser_add.add_argument(
        '-w', '--weight',
        type=float,
        default=0,
        help="tbd"
    )
    parser_add.add_argument(
        '-r', '--repeat',
        type=validate_time_period,
        help="Repetition period. Format examples: "
             "'X years' "
             "'X months' "
             "'X days' "
             "workdays"
    )
    parser_add.add_argument(
        '-d', '--date',
        default="today",
        type=validate_relative_date,
        help="Due date. Excepted formats:"
             "YYYY-MM-DD"
             "today [default]"
             "tomorrow"
             "'+X days'"
             "'+X months'"
             "'+X years'"
             "no"
    )

    # listing tasks
    parser_list = subparsers.add_parser('list', help='List tasks')
    list_group = parser_list.add_mutually_exclusive_group()
    list_group.add_argument(
        '-t', '--top',
        action='store_true',
        help="List the highest priority task today"
    )
    parser_list.add_argument(
        '-d', '--date',
        type=str,
        help="List open tasks at a given date. Format: YYYY-MM-DD"
    )
    list_group.add_argument(
        '-o', '--open',
        action='store_true',
        help="List open tasks"
    )

    # modifying tasks
    parser_mod = subparsers.add_parser('mod', help='Modify a task')
    parser_mod.add_argument(
        'id',
        type=str,
        help="Name of the task to add"
    )
    parser_mod.add_argument(
        '-n', '--name',
        type=str,
        default="",
        help="Name of the task"
    )
    parser_mod.add_argument(
        '-p', '--priority',
        type=int,
        default=-1,
        help="Priority of the task"
    )
    parser_mod.add_argument(
        '-t', '--time',
        type=validate_time,
        help="Start time of the task. Format HH:MM"
    )
    parser_mod.add_argument(
        '-w', '--weight',
        type=float,
        default=-1,
        help="tbd"
    )

    parser_mod.add_argument(
        '-r', '--repeat',
        type=validate_time_period,
        help="Repetition period. Format examples: "
             "'X days'"
             "'X months'"
             "'X years'"
             "workdays"
    )

    parser_mod.add_argument(
        '-d', '--date',
        type=validate_relative_date,
        help="Postpone the task. Excepted formats:"
             "YYYY-MM-DD"
             "today"
             "tomorrow"
             "'+X days'"
             "'+X months'"
             "'+X years'"
             "no"
    )

    # closing tasks
    parser_close = subparsers.add_parser('close', help='Mark a task as closed')
    parser_close.add_argument(
        'id',
        type=str,
        nargs='?',
        help="ID of the task to close"
    )

    # deleting tasks
    parser_delete = subparsers.add_parser('delete', help='Permanently delete a task')
    parser_delete.add_argument(
        'id',
        type=str,
        help="ID of the task to delete"
    )

    # reporting
    parser_report = subparsers.add_parser('report',
                                          help='Calculate a total weight of tasks. '
                                               'If no arguments specified - '
                                               'weight of all tasks today (both open and closed)')
    parser_report.add_argument(
        '-d', '--date',
        type=str,
        help="Total weight of tasks on a given date. Date format: YYYY-MM-DD"
    )
    parser_report.add_argument(
        '-o', '--open',
        action='store_true',
        help="Total weight of open tasks today"
    )
    parser_report.add_argument(
        '-p', '--plot',
        action='store_true',
        help="Build a plot of productivity by days"
    )

    # notes
    parser_note = subparsers.add_parser('note',
                                        help='Add a note for a given day')
    parser_note.add_argument(
        'text',
        type=str,
        help="The text of the note"
    )
    parser_note.add_argument(
        '-d', '--date',
        type=validate_date,
        help="Associate the note with a date."
             "Default: current date"
    )

    # RPG extension
    parser_rpg = subparsers.add_parser('rpg', help='tbd')
    rpg_group = parser_rpg.add_mutually_exclusive_group()
    rpg_group.add_argument(
        '-l', '--list-quests',
        action='store_true',
        help='tbd'
    )
    rpg_group.add_argument(
        '-f', '--finish-quest',
        type=int,
        help='tbd'
    )
    rpg_group.add_argument(
        '-a', '--list-awards',
        action='store_true',
        help='tbd'
    )
    rpg_group.add_argument(
        '-c', '--claim-award',
        type=int,
        default=0,
        help='tbd'
    )
    rpg_group.add_argument(
        '-p', '--character-parameters',
        action='store_true',
        help='tbd'
    )

    args = parser.parse_args()
    return args


# Argument validation

def validate_time(time_string: str):
    try:
        datetime.datetime.strptime(time_string, "%H:%M")
    except ValueError:
        raise ArgumentTypeError("Incorrect time format, should be HH:MM")
    return time_string


def validate_time_period(date_string: str):
    pattern = r"\d{1,3} (days|months|years)|workdays"
    result = re.search(pattern, date_string)

    if not result:
        raise ArgumentTypeError("Incorrect time format, should match " + pattern)
    return date_string


def validate_date(date_string: str):
    pattern = r"\d{4}-(0[1-9]|1[012])-([0-2]\d|3[0-1])"
    result = re.search(pattern, date_string)

    if not result:
        raise ArgumentTypeError("Incorrect time format, should match " + pattern)
    return date_string


def validate_relative_date(date_string: str):
    pattern = r"\d{4}-(0[1-9]|1[012])-([0-2]\d|3[0-1])|\+\d{1,3} (days|months|years)|today|tomorrow|no"
    result = re.search(pattern, date_string)

    if not result:
        raise ArgumentTypeError("Incorrect time format, should match " + pattern)
    return date_string


def set_logging(verbose=False):
    logging.basicConfig(
        format='[%(levelname)s] %(message)s',
        level=logging.INFO if not verbose else logging.DEBUG,
        datefmt="%m-%d %H:%M:%S"
    )


def print_tasks(tasks: list, verbose=True):
    if not tasks:
        logging.info("No open tasks")
        return

    # only the name of the task
    if not verbose and len(tasks) == 1:
        print("%s [%d]" % (tasks[0]["name"], tasks[0]["weight"]))
        return

    # description of a single task
    if verbose and len(tasks) == 1:
        t = tasks[0]
        due_time = t["due_time"] if t["due_time"] else "--:--"
        print("Pr: {:<3} | Status: {:<2} | Weight: {:<4} | Due: {} | ID: {:<3} | {}".format(
            t["priority"], t["status"], t["weight"], due_time, t["id"], t["name"]))
        return

    if verbose:
        print("PR  | ST | WEI  |  DUE  | ID  | Name\n-------------------------------------")

    for t in tasks:
        due_time = t["due_time"] if t["due_time"] else "--:--"
        print("{:<3} | {:<2} | {:<4} | {} | {:<3} | {}".format(
            t["priority"], t["status"], t["weight"], due_time, t["id"], t["name"]))


def ask_confirmation(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' "
                  "(or 'y' or 'n').\n")


def close(db, cursor, id_):
    if not id_:
        task = core.list_tasks(cursor, True, due_date="today")
        if not task:
            print("No open tasks")
            return
        id_ = task[0]["id"]
        name = task[0]["name"]
        if not ask_confirmation("Do you want to close \"%s\"?" % name):
            return

    name = core.close_task(db, cursor, id_)
    if not name:
        print("Canceled")
    else:
        print("Closed task: " + name)
        print("Next task:")
        tasks = core.list_tasks(cursor, True, due_date="today")
        print_tasks(tasks)


def main():
    set_logging()
    args = get_arguments()
    config = core.read_configuration()

    # Connect to DB
    database_file = config['db_path']
    db = sqlite3.connect(database_file)
    cursor = db.cursor()

    #
    # Execute the command:
    # add new task
    if args.subparser_name == 'add':
        core.add_task(db, cursor, args.name, args.priority, args.time, args.date, args.weight, args.repeat)
        print("Added '%s'; priority %s; due %s %s" % (args.name, args.priority, args.time, args.date))

    # list tasks
    elif args.subparser_name == 'list':
        if not args.date:
            # by default, list overdue tasks too
            tasks = core.list_tasks(cursor, args.top, args.open, due_date=args.date)
            print_tasks(tasks, args.verbose)
        else:
            tasks = core.list_tasks(cursor, args.top, args.open, exclude_overdue_tasks=True, due_date=args.date)
            print_tasks(tasks, args.verbose)

    # modify a task
    elif args.subparser_name == 'mod':
        core.modify_task(db, cursor, args.id, args.name, args.priority, args.time, args.weight, args.repeat, args.date)
        print("Task modified: " + args.id)

    # close a task
    elif args.subparser_name == 'close':
        close(db, cursor, args.id)

    # delete a task
    elif args.subparser_name == 'delete':
        core.delete_task(db, cursor, args.id)
        print("Task deleted: " + args.id)

    # add a note
    elif args.subparser_name == 'note':
        core.add_note(db, cursor, args.date, args.text)
        print("Note added")

    # report stats
    elif args.subparser_name == 'report':
        if args.plot:
            core.productivity_plot(cursor)
        else:
            weight = core.get_total_weight(cursor)
            print("Total weight:", weight)

    #
    # RPG extension:
    elif args.subparser_name == 'rpg':

        # list quests
        if args.list_quests:
            quests = rpg_mod.get_quests(cursor)
            print("ID  | XP | G  | Name \n-----------------")
            for q in quests:
                print("{:<3} | {:<2} | {:<2} | {}".format(q["id"], q["xp"], q["gold"], q["name"]))

        # close a quest
        elif args.finish_quest:
            result = rpg_mod.close_quest(db, cursor, args.finish_quest)
            if not result:
                print("Not such quest!")

            print("Closed quest: " + result[0])
            if result[1]:
                print("\n\n   Hey! You leveled up!!!\n")
            if result[2]:
                print("Skill " + result[3] + " increased to level " + result[4])

        # list available awards
        elif args.list_awards:
            awards = rpg_mod.get_awards(cursor)
            print("ID  | Price | Name\n---------------------")
            for a in awards:
                print("{:<3} | {:<5} | {}".format(a["id"], a["price"], a["name"]))

        # claim an award
        elif args.claim_award:
            result = rpg_mod.claim_award(db, cursor, args.claim_award)
            print("{} costed you {} gold".format(result[0], result[1]))
            print("Now you have " + result[2] + " gold")

        # print character parameters
        elif args.character_parameters:
            character = rpg_mod.get_character_stats(cursor)
            print("Level: {}\n"
                  "Gold: {}\n"
                  "XP: {} [next: {}]"
                  .format(character["level"], character["gold"], character["xp"], character["xp_for_next_level"]))

        # by default, print all useful info
        else:
            quests = rpg_mod.get_quests(cursor)
            print("  Quests")
            print("ID  | XP | G  | Name \n-----------------")
            for q in quests:
                print("{:<3} | {:<2} | {:<2} | {}".format(q["id"], q["xp"], q["gold"], q["name"]))

            awards = rpg_mod.get_awards(cursor)
            print("  Awards")
            print("ID  | Price | Name\n---------------------")
            for a in awards:
                print("{:<3} | {:<5} | {}".format(a["id"], a["price"], a["name"]))

            character = rpg_mod.get_character_stats(cursor)
            print("\nLevel: {}\n"
                  "Gold: {}\n"
                  "XP: {} [next: {}]"
                  .format(character["level"], character["gold"], character["xp"], character["xp_for_next_level"]))

    db.close()


if __name__ == '__main__':
    main()
