#!/usr/bin/env python3
import curses
from enum import Enum
import sqlite3

import rpg_mod
import core


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

        self.window.addstr(2, 2, "l: list tasks     n: add note        r: show reports")
        self.window.addstr(2, 2, "l", curses.A_BOLD)
        self.window.addstr(2, 20, "n", curses.A_BOLD)
        self.window.addstr(2, 39, "r", curses.A_BOLD)

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

        self.window.addstr(1, 2, "n: next task         p: previous task   s: select   u: undo selection")
        self.window.addstr(1, 2, "n", curses.A_BOLD)
        self.window.addstr(1, 23, "p", curses.A_BOLD)
        self.window.addstr(1, 42, "s", curses.A_BOLD)
        self.window.addstr(1, 54, "u", curses.A_BOLD)

        self.window.addstr(2, 2, "m: modify selected   h: go to home screen")
        self.window.addstr(2, 2, "m", curses.A_BOLD)
        self.window.addstr(2, 23, "h", curses.A_BOLD)

        self.window.addstr(3, 2, "o: include overdue   c: include closed              q: quit")
        self.window.addstr(3, 2, "o", curses.A_BOLD)
        self.window.addstr(3, 23, "c", curses.A_BOLD)
        self.window.addstr(3, 54, "q", curses.A_BOLD)

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
    ADD_NEW_TASK = 3
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
        curses.curs_set(False)

        while self.state != ScreenState.QUIT:
            if self.state == ScreenState.HOME:
                self.home()
            elif self.state == ScreenState.LIST_TASKS:
                self.tasks()
            elif self.state == ScreenState.ADD_NEW_TASK:
                pass

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
                self.message_window.print("Not implemented")
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
                self.message_window.print("Not implemented")
            elif c == 'r':
                self.message_window.print("Not implemented")
            elif c == 'u':
                self.message_window.print("Not implemented")
            elif c == 'w':
                self.message_window.print("Not implemented")

    def tasks(self):
        current_task = 0
        selected_tasks = set()

        # retrieve the tasks
        tasks = core.list_tasks(self.cursor, False)
        if not tasks:
            self.message_window.print("No open tasks!")
            self.state = ScreenState.HOME
            return

        # redraw windows
        self.main_window.draw_tasks(tasks)
        self.commands_window.draw_tasks()
        self.message_window.clear()
        self.main_window.draw_cursor(0, 0)

        # wait for commands
        while True:
            c = self.stdscr.getkey()
            self.message_window.clear()

            if c == 'q':
                self.state = ScreenState.QUIT
                break
            if c == 'n':
                previous_value = current_task
                current_task = (current_task + 1) % len(tasks)
                self.main_window.draw_cursor(current_task, previous_value)
            elif c == 'p':
                previous_value = current_task
                current_task = (current_task - 1) % len(tasks)
                self.main_window.draw_cursor(current_task, previous_value)
            elif c == 's':
                selected_tasks.add(current_task)
                self.main_window.draw_selection(current_task)
            elif c == 'u':
                selected_tasks.discard(current_task)
                self.main_window.draw_selection(current_task, True)
            elif c == 'm':
                if not selected_tasks:
                    self.message_window.print("No selected tasks!")
                    continue

                self.modify([tasks[i] for i in selected_tasks])
                break  # we have to reload all windows after modification
            elif c == 'h':
                self.state = ScreenState.HOME
                break
            elif c == 'o':
                tasks = core.list_tasks(self.cursor, False)
                tasks += core.list_tasks(self.cursor, False, list_overdue_tasks=True)
                selected_tasks.clear()
                current_task = 0
                self.main_window.draw_tasks(tasks)
                self.main_window.draw_cursor(0, 0)
            elif c == 'c':
                tasks = core.list_tasks(self.cursor, False, exclude_closed_tasks=False)
                selected_tasks.clear()
                current_task = 0
                self.main_window.draw_tasks(tasks)
                self.main_window.draw_cursor(0, 0)

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
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, time=time)
                    tasks[i]["time"] = time
                    self.main_window.draw_tasks(tasks, header="All these tasks will be modified")
                    self.message_window.clear()
            elif c == 'a':
                self.message_window.print("Not implemented!")
            elif c == 'e':
                self.message_window.print("Not implemented!")
            elif c == 'd':
                for i in ids:
                    core.delete_task(self.db, self.cursor, i)
                break


def main(stdscr):
    screen = Screen(stdscr)
    screen.start()


if __name__ == '__main__':
    curses.wrapper(main)
