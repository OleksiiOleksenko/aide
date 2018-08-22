#!/usr/bin/env python3
import curses
from enum import Enum
import sqlite3

import core
import rpg_mod
import project_mod


class MainWindow:
    def __init__(self, db: sqlite3.Connection, cursor: sqlite3.Cursor, stdscr):
        self.db = db
        self.cursor = cursor
        self.window = curses.newwin(30, curses.COLS - 1, 1, 0)
        self.stdscr = stdscr

    def draw_home(self):
        self.window.erase()
        self.window.addstr(0, 1, "Current task:")
        tasks = core.list_tasks(self.cursor, True)

        if not tasks:
            self.window.addstr(4, (curses.COLS // 2) - 8, "No open tasks!")
            self.stdscr.refresh()
            self.window.refresh()
            return

        top_task = tasks[0]
        self.window.addstr(2, 2, ">> " + top_task["name"] + " <<", curses.A_BOLD)
        self.window.addstr(3, 2, "Weight: {} | Priority : {} | ID: {} ".format(
            top_task["weight"], top_task["priority"], top_task["id"]))

        self.stdscr.refresh()
        self.window.refresh()

    def draw_tasks(self, tasks, header=""):
        self.window.erase()

        # list of today tasks
        self.window.addstr(0, 5, header, curses.A_BOLD)

        # table header
        self.window.addstr(1, 1, "Name")
        self.window.addstr(1, curses.COLS - 30, "|ST|PR |WGHT|Time |Date      ")
        self.window.hline(2, 0, curses.ACS_HLINE, curses.COLS - 1)

        # list of current tasks
        line = 3
        for t in tasks:
            due_time = t["due_time"] if t["due_time"] else "--:--"
            self.window.addstr(line, 2, t["name"])
            self.window.addstr(line, curses.COLS - 30, "|{:<2}|{:<3}|{:<1.2f}|{}|{}".format(
                t["status"], t["priority"], t["weight"], due_time, t["due_date"]))
            line += 1

        self.window.hline(line, 0, curses.ACS_HLINE, curses.COLS - 1)
        line += 1

        self.window.addstr(line, 2, "Here: ST - status; PR - priority; WGHT - weight")

        self.stdscr.refresh()
        self.window.refresh()

    def draw_cursor(self, new_position: int, old_position: int):
        offset = 3
        self.window.addstr(offset + old_position, 0, ' ')
        self.window.addstr(offset + new_position, 0, '>')
        self.stdscr.refresh()
        self.window.refresh()

    def draw_selection(self, position: int, unselect=False):
        offset = 3
        if unselect:
            self.window.addstr(offset + position, 1, ' ')
        else:
            self.window.addstr(offset + position, 1, '*')
        self.stdscr.refresh()
        self.window.refresh()

    def draw_quests(self, quests):
        self.window.erase()

        # table header
        self.window.addstr(1, 1, "Name")
        self.window.addstr(1, curses.COLS - 12, "|XP |Gold")
        self.window.hline(2, 0, curses.ACS_HLINE, curses.COLS - 1)

        # list of current tasks
        line = 3
        for q in quests:
            self.window.addstr(line, 2, q["name"])
            self.window.addstr(line, curses.COLS - 12, "|{:<3}|{:<4}".format(q["xp"], q["gold"]))
            line += 1

        self.window.hline(line, 0, curses.ACS_HLINE, curses.COLS - 1)
        line += 1

        self.stdscr.refresh()
        self.window.refresh()

    def draw_awards(self, awards):
        self.window.erase()

        # table header
        self.window.addstr(1, 1, "Name")
        self.window.addstr(1, curses.COLS - 7, "|Price")
        self.window.hline(2, 0, curses.ACS_HLINE, curses.COLS - 1)

        # list of current tasks
        line = 3
        for a in awards:
            self.window.addstr(line, 2, a["name"])
            self.window.addstr(line, curses.COLS - 7, "|{:<5}".format(a["price"]))
            line += 1

        self.window.hline(line, 0, curses.ACS_HLINE, curses.COLS - 1)
        line += 1

        self.stdscr.refresh()
        self.window.refresh()

    def draw_projects(self, projects):
        self.window.erase()

        # table header
        self.window.addstr(1, 1, "Name")
        self.window.addstr(1, curses.COLS - 10, "|Priority")
        self.window.hline(2, 0, curses.ACS_HLINE, curses.COLS - 1)

        # list of current tasks
        line = 3
        for p in projects:
            self.window.addstr(line, 2, p["name"])
            self.window.addstr(line, curses.COLS - 10, "|{:<8}".format(p["priority"]))
            line += 1

        self.window.hline(line, 0, curses.ACS_HLINE, curses.COLS - 1)
        line += 1

        self.stdscr.refresh()
        self.window.refresh()


class MessageWindow:
    def __init__(self, stdscr):
        self.window = curses.newwin(2, curses.COLS - 1, curses.LINES - 8, 0)
        self.stdscr = stdscr

    def print(self, text: str):
        self.window.addstr(0, 1, text)
        self.stdscr.refresh()
        self.window.refresh()

    def ask_confirmation(self, text: str, default=True):
        valid = {"y": True, "n": False}

        if default is None:
            prompt = " [y/n] "
        elif default is True:
            prompt = " [Y/n] "
        else:
            prompt = " [y/N] "

        while True:
            self.window.addstr(0, 1, text + prompt)
            self.stdscr.refresh()
            self.window.refresh()

            choice = self.stdscr.getkey()

            if default is not None and choice == '':
                return default
            elif choice in valid:
                return valid[choice]
            else:
                self.window.addstr(1, 1, "Please respond with 'y' or 'n'")
                self.stdscr.refresh()
                self.window.refresh()

    def clear(self):
        self.window.erase()
        self.stdscr.refresh()
        self.window.refresh()

    def get_input(self):
        curses.echo()

        self.window.addstr(1, 1, ">> ")
        self.stdscr.refresh()
        self.window.refresh()

        s = self.window.getstr(1, 5, 40)

        curses.noecho()
        return s.decode("utf-8")


class CommandsWindow:
    def __init__(self, stdscr):
        self.window = curses.newwin(5, curses.COLS - 1, curses.LINES - 6, 0)
        self.stdscr = stdscr

    def draw_home(self):
        self.window.erase()
        self.window.box()
        self.window.addstr(0, (curses.COLS // 2) - 11, " Available commands ")

        self.window.addstr(1, 2, "a: add task       m: modify current  c: close current    d: delete current")
        self.window.addstr(1, 2, "a", curses.A_BOLD)
        self.window.addstr(1, 20, "m", curses.A_BOLD)
        self.window.addstr(1, 39, "c", curses.A_BOLD)
        self.window.addstr(1, 59, "d", curses.A_BOLD)

        self.window.addstr(2, 2, "l: list tasks     n: add note        r: show reports     p: projects")
        self.window.addstr(2, 2, "l", curses.A_BOLD)
        self.window.addstr(2, 20, "n", curses.A_BOLD)
        self.window.addstr(2, 39, "r", curses.A_BOLD)
        self.window.addstr(2, 59, "p", curses.A_BOLD)

        self.window.addstr(3, 2, "u: quests         w: awards                              q: quit")
        self.window.addstr(3, 2, "u", curses.A_BOLD)
        self.window.addstr(3, 20, "w", curses.A_BOLD)
        self.window.addstr(3, 59, "q", curses.A_BOLD)

        self.stdscr.refresh()
        self.window.refresh()

    def draw_tasks(self):
        self.window.erase()
        self.window.box()
        self.window.addstr(0, (curses.COLS // 2) - 11, " Available commands ")

        self.window.addstr(1, 2, "n: next task        p: previous task    s: select           u: undo selection   ")
        self.window.addstr(1, 2, "n", curses.A_BOLD)
        self.window.addstr(1, 22, "p", curses.A_BOLD)
        self.window.addstr(1, 42, "s", curses.A_BOLD)
        self.window.addstr(1, 62, "u", curses.A_BOLD)

        self.window.addstr(2, 2, "a: add task         m: modify selected  h: higher prio.     l: lower prio.")
        self.window.addstr(2, 2, "a", curses.A_BOLD)
        self.window.addstr(2, 22, "m", curses.A_BOLD)
        self.window.addstr(2, 42, "h", curses.A_BOLD)
        self.window.addstr(2, 62, "l", curses.A_BOLD)

        self.window.addstr(3, 2, "o: exclude overdue  c: include closed   r: return           q: quit")
        self.window.addstr(3, 2, "o", curses.A_BOLD)
        self.window.addstr(3, 22, "c", curses.A_BOLD)
        self.window.addstr(3, 42, "r", curses.A_BOLD)
        self.window.addstr(3, 62, "q", curses.A_BOLD)

        self.stdscr.refresh()
        self.window.refresh()

    def draw_modify(self):
        self.window.erase()
        self.window.box()
        self.window.addstr(0, (curses.COLS // 2) - 11, " Available commands ")

        self.window.addstr(1, 2, "n: set name       s: set status      p: set priority   w: set weight")
        self.window.addstr(1, 2, "n", curses.A_BOLD)
        self.window.addstr(1, 20, "s", curses.A_BOLD)
        self.window.addstr(1, 39, "p", curses.A_BOLD)
        self.window.addstr(1, 57, "w", curses.A_BOLD)

        self.window.addstr(2, 2, "t: set due time   a: set due date    e: set repeat     d: delete tasks")
        self.window.addstr(2, 2, "t", curses.A_BOLD)
        self.window.addstr(2, 20, "a", curses.A_BOLD)
        self.window.addstr(2, 39, "e", curses.A_BOLD)
        self.window.addstr(2, 57, "d", curses.A_BOLD)

        self.window.addstr(3, 2, "r: return                                              q: quit")
        self.window.addstr(3, 2, "r", curses.A_BOLD)
        self.window.addstr(3, 57, "q", curses.A_BOLD)

        self.stdscr.refresh()
        self.window.refresh()

    def draw_quests(self):
        self.window.erase()
        self.window.box()
        self.window.addstr(0, (curses.COLS // 2) - 11, " Available commands ")

        self.window.addstr(1, 2, "n: next task         p: previous task")
        self.window.addstr(1, 2, "n", curses.A_BOLD)
        self.window.addstr(1, 23, "p", curses.A_BOLD)

        self.window.addstr(2, 2, "c: close quests")
        self.window.addstr(2, 2, "c", curses.A_BOLD)

        self.window.addstr(3, 2, "r: return to home screen                            q: quit")
        self.window.addstr(3, 2, "r", curses.A_BOLD)
        self.window.addstr(3, 54, "q", curses.A_BOLD)

        self.stdscr.refresh()
        self.window.refresh()

    def draw_awards(self):
        self.window.erase()
        self.window.box()
        self.window.addstr(0, (curses.COLS // 2) - 11, " Available commands ")

        self.window.addstr(1, 2, "n: next award         p: previous award")
        self.window.addstr(1, 2, "n", curses.A_BOLD)
        self.window.addstr(1, 24, "p", curses.A_BOLD)

        self.window.addstr(2, 2, "c: claim award")
        self.window.addstr(2, 2, "c", curses.A_BOLD)

        self.window.addstr(3, 2, "r: return to home screen                            q: quit")
        self.window.addstr(3, 2, "r", curses.A_BOLD)
        self.window.addstr(3, 54, "q", curses.A_BOLD)

        self.stdscr.refresh()
        self.window.refresh()

    def draw_projects(self):
        self.window.erase()
        self.window.box()
        self.window.addstr(0, (curses.COLS // 2) - 11, " Available commands ")

        self.window.addstr(1, 2, "n: next project         p: previous project")
        self.window.addstr(1, 2, "n", curses.A_BOLD)
        self.window.addstr(1, 26, "p", curses.A_BOLD)

        self.window.addstr(2, 2, "l: list tasks           e: set priority             a: add project")
        self.window.addstr(2, 2, "l", curses.A_BOLD)
        self.window.addstr(2, 26, "e", curses.A_BOLD)
        self.window.addstr(2, 54, "a", curses.A_BOLD)

        self.window.addstr(3, 2, "r: return                                           q: quit")
        self.window.addstr(3, 2, "r", curses.A_BOLD)
        self.window.addstr(3, 54, "q", curses.A_BOLD)

        self.stdscr.refresh()
        self.window.refresh()

    def draw_tasks_in_project(self):
        self.window.erase()
        self.window.box()
        self.window.addstr(0, (curses.COLS // 2) - 11, " Available commands ")

        self.window.addstr(1, 2, "n: next project     p: previous proj.   h: higer prio.      l: lower prio.")
        self.window.addstr(1, 2, "n", curses.A_BOLD)
        self.window.addstr(1, 22, "p", curses.A_BOLD)
        self.window.addstr(1, 42, "h", curses.A_BOLD)
        self.window.addstr(1, 62, "l", curses.A_BOLD)

        self.window.addstr(2, 2, "t: set for today    o: remove due date  a: add task to project")
        self.window.addstr(2, 2, "t", curses.A_BOLD)
        self.window.addstr(2, 22, "o", curses.A_BOLD)
        self.window.addstr(2, 42, "a", curses.A_BOLD)

        self.window.addstr(3, 2, "                                        r: return           q: quit")
        self.window.addstr(3, 42, "r", curses.A_BOLD)
        self.window.addstr(3, 62, "q", curses.A_BOLD)

        self.stdscr.refresh()
        self.window.refresh()


class ProgressWindow:
    def __init__(self, db: sqlite3.Connection, cursor: sqlite3.Cursor, stdscr):
        self.db = db
        self.cursor = cursor
        self.window = curses.newwin(3, 25, curses.LINES - 1, 0)
        self.stdscr = stdscr

    def draw(self):
        weight_total = core.get_total_weight(self.cursor)
        weight_current = core.get_total_weight(self.cursor, True)
        self.window.addstr(0, 0, "Progress: {:.2f} / {:.2f}".format(weight_current, weight_total))
        self.stdscr.refresh()
        self.window.refresh()


class CharacterWindow:
    def __init__(self, db: sqlite3.Connection, cursor: sqlite3.Cursor, stdscr):
        self.db = db
        self.cursor = cursor
        self.window = curses.newwin(3, 42, curses.LINES - 1, curses.COLS - 42)
        self.stdscr = stdscr

    def draw(self):
        character = rpg_mod.get_character_stats(self.cursor)
        self.window.addstr(0, 0, "Level: {:<3} | XP: {:>4} / {:<4} | Gold: {:<4}".format(
            character["level"], character["xp"], character["xp_for_next_level"], character["gold"]))
        self.stdscr.refresh()
        self.window.refresh()


class ScreenState(Enum):
    HOME = 1
    LIST_TASKS = 2
    QUESTS = 3
    AWARDS = 4
    PROJECTS = 5
    QUIT = 0


class Screen:
    state = ScreenState.HOME

    def __init__(self, stdscr):
        # connect to the db
        config = core.read_configuration()
        database_file = config['db_path']
        db = sqlite3.connect(database_file)
        cursor = db.cursor()

        # initialize windows
        self.main_window = MainWindow(db, cursor, stdscr)
        self.message_window = MessageWindow(stdscr)
        self.commands_window = CommandsWindow(stdscr)
        self.progress_window = ProgressWindow(db, cursor, stdscr)
        self.character_window = CharacterWindow(db, cursor, stdscr)

        self.stdscr = stdscr
        self.db = db
        self.cursor = cursor

    def start(self):
        # clear screen
        self.stdscr.clear()
        try:
            curses.curs_set(False)
        except curses.error:
            pass

        while self.state != ScreenState.QUIT:
            if self.state == ScreenState.HOME:
                self.home()
            elif self.state == ScreenState.LIST_TASKS:
                self.tasks()
            elif self.state == ScreenState.QUESTS:
                self.quests()
            elif self.state == ScreenState.AWARDS:
                self.awards()
            elif self.state == ScreenState.PROJECTS:
                self.projects()

    def home(self):
        # retrieve the current task
        tasks = core.list_tasks(self.cursor, True)

        # redraw windows
        self.main_window.draw_home()
        self.commands_window.draw_home()
        self.progress_window.draw()
        self.character_window.draw()
        self.message_window.clear()

        # wait for commands
        while True:
            c = self.stdscr.getkey()
            self.message_window.clear()

            if c == 'q':
                self.state = ScreenState.QUIT
                break
            elif c == 'a':
                if self.add_task():
                    break  # we have to reload all windows after modification
                else:
                    continue  # no need to reload if task wasn't added
            elif c == 'm':
                if not tasks:
                    self.message_window.print("No task to modify")
                    continue

                self.modify(tasks)
                break  # we have to reload all windows after modification
            elif c == 'c':
                if not tasks:
                    self.message_window.print("No task to close")
                    continue

                if self.message_window.ask_confirmation("Do you want to close the current task?"):
                    core.close_task(self.db, self.cursor, tasks[0]["id"])
                    break
            elif c == 'd':
                if not tasks:
                    self.message_window.print("No task to delete")
                    continue

                if self.message_window.ask_confirmation("Do you want to delete the current task?"):
                    core.delete_task(self.db, self.cursor, tasks[0]["id"])
                    break
            elif c == 'l':
                self.state = ScreenState.LIST_TASKS
                break
            elif c == 'n':
                self.message_window.print("Enter the note:")
                text = self.message_window.get_input()

                self.message_window.clear()
                self.message_window.print("Enter the date (YYYY-MM-DD):")
                date = self.message_window.get_input()
                if not core.validate_date(date):
                    self.message_window.print("Wrong date format. Aborted.")
                    continue

                core.add_note(self.db, self.cursor, date, text)
                self.message_window.clear()
                self.message_window.print("Note added")
            elif c == 'r':
                core.productivity_plot(self.cursor)
            elif c == 'u':
                self.state = ScreenState.QUESTS
                break
            elif c == 'w':
                self.state = ScreenState.AWARDS
                break
            elif c == 'p':
                self.state = ScreenState.PROJECTS
                break

    def tasks(self):
        current = 0
        selected_tasks = set()

        redraw = True
        include_overdue = True
        include_closed = False

        # wait for commands
        while True:
            if redraw:
                if include_closed:
                    tasks = core.list_tasks(self.cursor, False)
                else:
                    tasks = core.list_tasks(self.cursor, False, exclude_closed_tasks=True)
                if include_overdue:
                    tasks += core.list_tasks(self.cursor, False, list_overdue_tasks=True)
                if not tasks:
                    self.message_window.print("No open tasks!")

                selected_tasks.clear()
                current = 0

                self.main_window.draw_tasks(tasks)
                self.commands_window.draw_tasks()
                self.progress_window.draw()
                self.main_window.draw_cursor(0, 0)
                redraw = False

            c = self.stdscr.getkey()
            self.message_window.clear()

            if c == 'q':
                self.state = ScreenState.QUIT
                break
            elif c == 'r':
                self.state = ScreenState.HOME
                break
            if c == 'n':
                previous_value = current
                current = (current + 1) % len(tasks)
                self.main_window.draw_cursor(current, previous_value)
            elif c == 'p':
                previous_value = current
                current = (current - 1) % len(tasks)
                self.main_window.draw_cursor(current, previous_value)
            elif c == 's':
                selected_tasks.add(current)
                self.main_window.draw_selection(current)
            elif c == 'u':
                selected_tasks.discard(current)
                self.main_window.draw_selection(current, True)
            elif c == 'm':
                if not selected_tasks:
                    self.message_window.print("No selected tasks!")
                    continue
                self.modify([tasks[i] for i in selected_tasks])
                redraw = True  # we have to reload all windows after modification
            elif c == 'o':
                include_overdue = False
                redraw = True
            elif c == 'c':
                include_closed = True
                redraw = True
            elif c == 'a':
                self.add_task()
                redraw = True  # we have to reload all windows after modification
            elif c == 'h':
                task = tasks[current]
                new_priority = task["priority"] + 5
                core.modify_task(self.db, self.cursor, task["id"], priority=new_priority)
                redraw = True
            elif c == 'l':
                task = tasks[current]
                new_priority = task["priority"] - 5 if task["priority"] >= 5 else 0
                core.modify_task(self.db, self.cursor, task["id"], priority=new_priority)
                redraw = True

    def modify(self, tasks):
        ids = [t["id"] for t in tasks]

        # redraw windows
        self.main_window.draw_tasks(tasks, header="All these tasks will be modified")
        self.commands_window.draw_modify()
        self.message_window.clear()

        # wait for commands
        while True:
            c = self.stdscr.getkey()
            self.message_window.clear()

            if c == 'q':
                self.state = ScreenState.QUIT
                break
            elif c == 'r':
                return
            elif c == 'n':
                self.message_window.print("Enter new name:")
                name = self.message_window.get_input()
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, name=name)
                    tasks[i]["name"] = name
                self.main_window.draw_tasks(tasks, header="All these tasks will be modified")
                self.message_window.clear()
            elif c == 's':
                self.message_window.print("Enter new status, 0 - closed, 1 - open:")
                status = int(self.message_window.get_input())
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, status=status)
                    tasks[i]["status"] = status
                self.main_window.draw_tasks(tasks, header="All these tasks will be modified")
                self.message_window.clear()
            elif c == 'p':
                self.message_window.print("Enter new priority:")
                priority = int(self.message_window.get_input())
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, priority=priority)
                    tasks[i]["priority"] = priority
                self.main_window.draw_tasks(tasks, header="All these tasks will be modified")
                self.message_window.clear()
            elif c == 'w':
                self.message_window.print("Enter new weight:")
                weight = float(self.message_window.get_input())
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, weight=weight)
                    tasks[i]["weight"] = weight
                self.main_window.draw_tasks(tasks, header="All these tasks will be modified")
                self.message_window.clear()
            elif c == 't':
                self.message_window.print("Enter new time (HH:MM):")
                time = self.message_window.get_input()
                if not core.validate_time(time):
                    self.message_window.print("Wrong time format. Aborted.")
                    break

                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, time=time)
                    tasks[i]["time"] = time
                self.main_window.draw_tasks(tasks, header="All these tasks will be modified")
                self.message_window.clear()
            elif c == 'a':
                self.message_window.print("Enter new due date (YYYY-MM-DD):")
                date = self.message_window.get_input()
                if not core.validate_relative_date(date):
                    self.message_window.print("Wrong date format. Aborted.")
                    break

                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, due_date=date)
                    tasks[i]["due_date"] = date
                self.main_window.draw_tasks(tasks, header="All these tasks will be modified")
                self.message_window.clear()
            elif c == 'e':
                self.message_window.print("Enter repetition period (no repetition if left blank):")
                repeat = self.message_window.get_input()
                if not core.validate_time_period(repeat):
                    self.message_window.print("Wrong period format. Aborted.")
                    break

                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, repeat=repeat)
                    tasks[i]["repeat"] = repeat
                self.main_window.draw_tasks(tasks, header="All these tasks will be modified")
                self.message_window.clear()
            elif c == 'd':
                if self.message_window.ask_confirmation("Do you want to delete the tasks?"):
                    for i in ids:
                        core.delete_task(self.db, self.cursor, i)
                    break

    def add_task(self, due_date: str = "", due_time: str = "", project: int = None):
        self.message_window.print("Enter the task:")
        name = self.message_window.get_input()
        self.message_window.clear()

        # priority
        self.message_window.print("Enter task priority (0 if left blank):")
        priority = self.message_window.get_input()
        priority = int(priority) if priority else 0
        self.message_window.clear()

        # weight
        self.message_window.print("Enter task weight (0.0 if left blank):")
        weight = self.message_window.get_input()
        weight = float(weight) if weight else 0.0
        self.message_window.clear()

        # due date
        if due_date == "":
            self.message_window.print("Enter due date (YYYY-MM-DD) (today if left blank):")
            due_date = self.message_window.get_input()
            if not core.validate_relative_date(due_date):
                self.message_window.print("Wrong date format. Aborted.")
                return False
            self.message_window.clear()

        # due time
        if due_time == "":
            self.message_window.print("Enter due time (HH:MM) (00:00 if left blank):")
            due_time = self.message_window.get_input()
            if not core.validate_time(due_time):
                self.message_window.print("Wrong time format. Aborted.")
                return False
            self.message_window.clear()

        # repeat period
        self.message_window.print("Enter repetition period (no repetition if left blank):")
        repeat = self.message_window.get_input()
        if not core.validate_time_period(repeat):
            self.message_window.print("Wrong period format. Aborted.")
            return False
        self.message_window.clear()

        core.add_task(self.db, self.cursor, name, priority, due_time, due_date, weight, repeat, project=project)
        return True

    def quests(self):
        # retrieve the quests
        quests = rpg_mod.get_quests(self.cursor)
        current_quest = 0

        # redraw windows
        self.main_window.draw_quests(quests)
        self.commands_window.draw_quests()
        self.progress_window.draw()
        self.character_window.draw()
        self.main_window.draw_cursor(0, 0)

        # wait for commands
        while True:
            c = self.stdscr.getkey()
            self.message_window.clear()

            if c == 'q':
                self.state = ScreenState.QUIT
                break
            elif c == 'r':
                self.state = ScreenState.HOME
                break
            if c == 'n':
                previous_value = current_quest
                current_quest = (current_quest + 1) % len(quests)
                self.main_window.draw_cursor(current_quest, previous_value)
            elif c == 'p':
                previous_value = current_quest
                current_quest = (current_quest - 1) % len(quests)
                self.main_window.draw_cursor(current_quest, previous_value)
            elif c == 'c':
                result = rpg_mod.close_quest(self.db, self.cursor, quests[current_quest]["id"])
                message = "Closed quest: " + result[0]
                if result[2]:
                    message = "Skill " + result[3] + " increased to level " + result[4]
                if result[1]:
                    message = "Hey! You leveled up!!!"
                self.message_window.print(message)
                break

    def awards(self):
        # retrieve the quests
        awards = rpg_mod.get_awards(self.cursor)
        current_award = 0

        # redraw windows
        self.main_window.draw_awards(awards)
        self.commands_window.draw_awards()
        self.character_window.draw()
        self.main_window.draw_cursor(0, 0)

        # wait for commands
        while True:
            c = self.stdscr.getkey()
            self.message_window.clear()

            if c == 'q':
                self.state = ScreenState.QUIT
                break
            elif c == 'r':
                self.state = ScreenState.HOME
                break
            if c == 'n':
                previous_value = current_award
                current_award = (current_award + 1) % len(awards)
                self.main_window.draw_cursor(current_award, previous_value)
            elif c == 'p':
                previous_value = current_award
                current_award = (current_award - 1) % len(awards)
                self.main_window.draw_cursor(current_award, previous_value)
            elif c == 'c':
                result = rpg_mod.claim_award(self.db, self.cursor, awards[current_award]["id"])
                self.message_window.print("{} costed you {} gold".format(result[0], result[1]))
                break

    def projects(self):
        # retrieve the quests
        projects = project_mod.list_projects(self.cursor)
        current = 0

        # redraw windows
        self.main_window.draw_projects(projects)
        self.commands_window.draw_projects()
        self.progress_window.draw()
        self.main_window.draw_cursor(0, 0)

        # wait for commands
        while True:
            c = self.stdscr.getkey()
            self.message_window.clear()

            if c == 'q':
                self.state = ScreenState.QUIT
                break
            elif c == 'r':
                self.state = ScreenState.HOME
                break
            elif c == 'n':
                previous_value = current
                current = (current + 1) % len(projects)
                self.main_window.draw_cursor(current, previous_value)
            elif c == 'p':
                previous_value = current
                current = (current - 1) % len(projects)
                self.main_window.draw_cursor(current, previous_value)
            elif c == 'l':
                self.tasks_in_project(projects[current]["id"])
                break
            elif c == 'e':
                self.message_window.print("Enter priority:")
                priority = self.message_window.get_input()
                if not priority:
                    self.message_window.print("Aborted")
                    continue
                project_mod.modify_project(self.db, self.cursor, projects[current]["id"], priority=priority)
                break
            elif c == 'a':
                self.message_window.print("Enter the name:")
                name = self.message_window.get_input()
                self.message_window.clear()

                self.message_window.print("Enter priority (0 if left blank):")
                priority = self.message_window.get_input()
                priority = int(priority) if priority else 0
                self.message_window.clear()

                project_mod.add_project(self.db, self.cursor, name, priority)
                break

    def tasks_in_project(self, id_):
        redraw = True
        include_overdue = True
        include_no_date = True
        current = 0

        # wait for commands
        while True:
            if redraw:
                tasks = core.list_tasks(self.cursor, project=id_)
                if include_overdue:
                    tasks += core.list_tasks(self.cursor, project=id_, list_overdue_tasks=True)
                if include_no_date:
                    tasks += core.list_tasks(self.cursor, project=id_, due_date="no")
                current = 0

                self.main_window.draw_tasks(tasks)
                self.commands_window.draw_tasks_in_project()
                self.progress_window.draw()
                self.main_window.draw_cursor(0, 0)
                redraw = False

            c = self.stdscr.getkey()
            self.message_window.clear()

            if c == 'q':
                self.state = ScreenState.QUIT
                break
            elif c == 'r':
                break
            elif c == 'n':
                previous_value = current
                current = (current + 1) % len(tasks)
                self.main_window.draw_cursor(current, previous_value)
            elif c == 'p':
                previous_value = current
                current = (current - 1) % len(tasks)
                self.main_window.draw_cursor(current, previous_value)
            elif c == 't':
                core.modify_task(self.db, self.cursor, tasks[current]["id"], due_date="today")
                redraw = True
            elif c == 'o':
                core.modify_task(self.db, self.cursor, tasks[current]["id"], due_date="no")
                redraw = True
            elif c == 'a':
                if self.add_task(project=id_, due_date="no", due_time=None):
                    redraw = True  # we have to reload all windows after modification
                else:
                    continue  # no need to reload if task wasn't added
            elif c == 'h':
                task = tasks[current]
                core.modify_task(self.db, self.cursor, task["id"], priority=task["priority"] + 5)
                redraw = True
            elif c == 'l':
                task = tasks[current]
                new_priority = task["priority"] - 5 if task["priority"] >= 5 else 0
                core.modify_task(self.db, self.cursor, task["id"], priority=new_priority)
                redraw = True


def main(stdscr):
    screen = Screen(stdscr)
    screen.start()


if __name__ == '__main__':
    curses.wrapper(main)
