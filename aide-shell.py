#!/usr/bin/env python3
import curses
import sqlite3

import core
import rpg_mod
import project_mod


class CallStack(list):
    def push(self, tab_class, args: list):
        self.append((tab_class, args))

    def is_empty(self):
        return not self

    def top_tab(self):
        return self[-1][0]

    def top_arguments(self):
        return self[-1][1]


class Tab:
    def __init__(self, call_stack: CallStack, db: sqlite3.Connection, cursor: sqlite3.Cursor, stdscr,
                 main_window, message_window, commands_window, progress_window, character_window):
        self.call_stack = call_stack
        self.db = db
        self.cursor = cursor
        self.stdscr = stdscr
        self.main_window = main_window
        self.message_window = message_window
        self.commands_window = commands_window
        self.progress_window = progress_window
        self.character_window = character_window

    def open(self) -> CallStack:
        pass

    def draw_all(self):
        self.draw_main()
        self.clear_messages()
        self.draw_commands()
        self.draw_progress_bar()
        self.draw_character_bar()

    def draw_main(self):
        pass

    def draw_commands(self):
        pass

    def draw_generic_commands(self, commands):
        self.commands_window.erase()
        self.commands_window.box()
        self.commands_window.addstr(0, (curses.COLS // 2) - 11, " Available commands ")

        line = 1
        for row in commands:
            position = 2
            for c in row:
                self.commands_window.addstr(line, position, c[0], curses.A_BOLD)
                self.commands_window.addstr(line, position + 1, ":" + c[1] if c[1] else "")
                position += 20
            line += 1

        self.stdscr.refresh()
        self.commands_window.refresh()

    def draw_progress_bar(self):
        weight_total = core.get_total_weight(self.cursor)
        weight_current = core.get_total_weight(self.cursor, True)
        self.progress_window.addstr(0, 0, "Progress: {:.2f} / {:.2f}".format(weight_current, weight_total))
        self.stdscr.refresh()
        self.progress_window.refresh()

    def draw_character_bar(self):
        character = rpg_mod.get_character_stats(self.cursor)
        self.character_window.addstr(0, 0, "Level: {:<3} | XP: {:>4} / {:<4} | Gold: {:<4}".format(
            character["level"], character["xp"], character["xp_for_next_level"], character["gold"]))
        self.stdscr.refresh()
        self.character_window.refresh()

    def draw_cursor(self, new_position: int, old_position: int):
        offset = 3
        self.main_window.addstr(offset + old_position, 0, ' ')
        self.main_window.addstr(offset + new_position, 0, '>')
        self.stdscr.refresh()
        self.main_window.refresh()

    def draw_selection(self, position: int, unselect=False):
        offset = 3
        if unselect:
            self.main_window.addstr(offset + position, 1, ' ')
        else:
            self.main_window.addstr(offset + position, 1, '*')
        self.stdscr.refresh()
        self.main_window.refresh()

    def print_message(self, text: str):
        self.message_window.addstr(0, 1, text)
        self.stdscr.refresh()
        self.message_window.refresh()

    def ask_confirmation(self, text: str, default=True):
        valid = {"y": True, "n": False}

        if default is None:
            prompt = " [y/n] "
        elif default is True:
            prompt = " [Y/n] "
        else:
            prompt = " [y/N] "

        while True:
            self.message_window.addstr(0, 1, text + prompt)
            self.stdscr.refresh()
            self.message_window.refresh()

            choice = self.stdscr.getkey()

            if default is not None and choice == '':
                return default
            elif choice in valid:
                return valid[choice]
            else:
                self.message_window.addstr(1, 1, "Please respond with 'y' or 'n'")
                self.stdscr.refresh()
                self.message_window.refresh()

    def clear_messages(self):
        self.message_window.erase()
        self.stdscr.refresh()
        self.message_window.refresh()

    def get_input(self):
        self.message_window.move(1, 1)

        s = ""
        while True:
            self.message_window.deleteln()
            self.message_window.addstr(1, 1, ">> " + s)
            self.message_window.refresh()
            self.stdscr.refresh()

            c = self.message_window.getch()
            if c == 27:
                s = None
                break

            if c == curses.KEY_ENTER or c == 10 or c == 13:
                break

            if c == curses.KEY_BACKSPACE or c == 127 or c == curses.KEY_DC:
                s = s[:-1]
                continue

            s += chr(c)

        return s

    def add_task(self, due_date: str = "", due_time: str = "", project: int = None):
        self.print_message("Enter the task:")
        name = self.get_input()
        if name is None:
            return
        self.message_window.clear()

        # priority
        self.print_message("Enter task priority (0 if left blank):")
        priority = self.get_input()
        if priority is None:
            return
        priority = int(priority) if priority else 0
        self.message_window.clear()

        # weight
        self.print_message("Enter task weight (0.0 if left blank):")
        weight = self.get_input()
        if weight is None:
            return
        weight = float(weight) if weight else 0.0
        self.message_window.clear()

        # due date
        if due_date == "":
            self.print_message("Enter due date (YYYY-MM-DD) (today if left blank):")
            due_date = self.get_input()
            if due_date is None:
                return

            if not core.validate_relative_date(due_date):
                self.print_message("Wrong date format. Aborted.")
                return False
            self.message_window.clear()

        # due time
        if due_time == "":
            self.print_message("Enter due time (HH:MM) (00:00 if left blank):")
            due_time = self.get_input()
            if due_time is None:
                return

            if not core.validate_time(due_time):
                self.print_message("Wrong time format. Aborted.")
                return False
            self.message_window.clear()

        # repeat period
        self.print_message("Enter repetition period (no repetition if left blank):")
        repeat = self.get_input()
        if repeat is None:
            return

        if not core.validate_time_period(repeat):
            self.print_message("Wrong period format. Aborted.")
            return False
        self.message_window.clear()

        core.add_task(self.db, self.cursor, name, priority, due_time, due_date, weight, repeat, project=project)
        return True

    def process_navigation_commands(self, command: str, navigation: dict, enable_return: bool = True):
        if command == 'q':
            self.call_stack.clear()
            return True

        if enable_return and command == 'r':
            self.call_stack.pop()
            return True

        if navigation.get(command, None):
            next_tab = navigation[command][0]
            arguments = navigation[command][1]()
            self.call_stack.push(next_tab, arguments)
            return True


class ListTab(Tab):
    def draw_list(self, list_, columns_header: str, column_format: str, column_fields):
        self.main_window.erase()

        # table header
        self.main_window.addstr(1, 1, "Name")
        self.main_window.addstr(1, curses.COLS - len(columns_header) - 1, columns_header)
        self.main_window.hline(2, 0, curses.ACS_HLINE, curses.COLS - 1)

        # list
        line = 3
        for element in list_:
            self.main_window.addstr(line, 2, element["name"])
            self.main_window.addstr(
                line,
                curses.COLS - len(columns_header) - 1,
                column_format.format(*(element[f] for f in column_fields))
            )
            line += 1

        if not list_:
            line += 1

        self.main_window.hline(line, 0, curses.ACS_HLINE, curses.COLS - 1)
        line += 1

        self.stdscr.refresh()
        self.main_window.refresh()


class HomeTab(Tab):
    task = None

    def open(self):
        navigation = {
            "l": (TaskListTab, lambda: []),
            "u": (QuestsListTab, lambda: []),
            "w": (AwardsListTab, lambda: []),
            "p": (ProjectListTab, lambda: []),
            "m": (ModifyTab, lambda: [self.task] if self.task else [])
        }

        redraw = True
        while True:
            if redraw:
                # retrieve the current task and update windows
                self.task = core.list_tasks(self.cursor, True)
                self.task = self.task[0] if self.task else None
                self.draw_all()
                redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process normal command
            if c == 'a':
                self.add_task()
                redraw = True
            elif c == 'c':
                if not self.task:
                    self.print_message("No task to close")
                    continue

                if self.ask_confirmation("Do you want to close the current task?"):
                    core.close_task(self.db, self.cursor, self.task["id"])
                redraw = True
            elif c == 'd':
                if not self.task:
                    self.print_message("No task to delete")
                    continue

                if self.ask_confirmation("Do you want to delete the current task?"):
                    core.delete_task(self.db, self.cursor, self.task["id"])
                redraw = True
            elif c == 'n':
                self.add_note()
            elif c == 'r':
                core.productivity_plot(self.cursor)

            if self.process_navigation_commands(c, navigation, enable_return=False):
                return self.call_stack

    def add_note(self):
        self.print_message("Enter the note:")
        text = self.get_input()
        if text is None:
            self.clear_messages()
            return

        self.clear_messages()
        self.print_message("Enter the date (YYYY-MM-DD):")
        date = self.get_input()
        if date is None:
            self.clear_messages()
            return
        if not core.validate_date(date):
            self.print_message("Wrong date format. Aborted.")
            return

        core.add_note(self.db, self.cursor, date, text)
        self.clear_messages()
        self.print_message("Note added")

    def draw_main(self):
        self.main_window.erase()
        self.main_window.addstr(0, 1, "Current task:")
        tasks = core.list_tasks(self.cursor, True)

        if not tasks:
            self.main_window.addstr(4, (curses.COLS // 2) - 8, "No open tasks!")
            self.stdscr.refresh()
            self.main_window.refresh()
            return

        top_task = tasks[0]
        self.main_window.addstr(2, 2, ">> " + top_task["name"] + " <<", curses.A_BOLD)
        self.main_window.addstr(3, 2, "Weight: {} | Priority : {} | ID: {} ".format(
            top_task["weight"], top_task["priority"], top_task["id"]))

        self.stdscr.refresh()
        self.main_window.refresh()

    def draw_commands(self):
        self.draw_generic_commands([
            [("a", "add task"), ("m", "modify current"), ("c", "close current"), ("d", "delete current")],
            [("l", "list tasks"), ("n", "add note"), ("r", "show reports"), ("p", "projects")],
            [("u", "quests"), ("w", "awards"), ("", ""), ("q", "quit")],
        ])


class TaskListTab(ListTab):
    tasks = []
    selected_tasks = set()

    def open(self):
        navigation = {
            "m": (ModifyTab, lambda: [self.tasks[i] for i in self.selected_tasks] if self.selected_tasks else [])
        }
        current = 0
        redraw = True
        include_overdue = True
        include_closed = False

        while True:
            if redraw:
                if include_closed:
                    self.tasks = core.list_tasks(self.cursor, False, exclude_closed_tasks=False)
                else:
                    self.tasks = core.list_tasks(self.cursor, False, exclude_closed_tasks=True)
                if include_overdue:
                    self.tasks += core.list_tasks(self.cursor, False, list_overdue_tasks=True)
                if not self.tasks:
                    self.print_message("No open tasks!")

                current = 0
                self.selected_tasks.clear()

                self.draw_all()
                self.draw_cursor(0, 0)
                redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == 'n':
                previous = current
                current = (current + 1) % len(self.tasks)
                self.draw_cursor(current, previous)
            elif c == 'p':
                previous = current
                current = (current - 1) % len(self.tasks)
                self.draw_cursor(current, previous)
            elif c == 's':
                self.selected_tasks.add(current)
                self.draw_selection(current)
            elif c == 'u':
                self.selected_tasks.discard(current)
                self.draw_selection(current, True)
            elif c == 'o':
                include_overdue = False
                redraw = True
            elif c == 'c':
                include_closed = True
                redraw = True
            elif c == 'a':
                self.add_task()
                redraw = True
            elif c == 'h':
                task = self.tasks[current]
                new_priority = task["priority"] + 5
                core.modify_task(self.db, self.cursor, task["id"], priority=new_priority)
                redraw = True
            elif c == 'l':
                task = self.tasks[current]
                new_priority = task["priority"] - 5 if task["priority"] >= 5 else 0
                core.modify_task(self.db, self.cursor, task["id"], priority=new_priority)
                redraw = True

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def draw_main(self):
        self.draw_list(
            self.tasks,
            "|ST|PR |WGHT|Time |Date      ",
            "|{0:<2}|{1:<3}|{2:<1.2f}|{3!s:5}|{4}",
            ("status", "priority", "weight", "due_time", "due_date"),
        )

    def draw_commands(self):
        self.draw_generic_commands([
            [("n", "next task"), ("p", "previous task"), ("s", "select "), ("u", "undo selection")],
            [("a", "add task"), ("m", "modify selected"), ("h", "higher prio."), ("l", "lower prio.")],
            [("o", "exclude overdue"), ("c", "include closed"), ("r", "return"), ("q", "quit")],
        ])


class QuestsListTab(ListTab):
    quests = []

    def open(self):
        navigation = {}
        current = 0
        redraw = True

        while True:
            if redraw:
                # retrieve the quests
                self.quests = rpg_mod.get_quests(self.cursor)

                current = 0
                self.draw_all()
                self.draw_cursor(0, 0)
                redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == 'n':
                previous = current
                current = (current + 1) % len(self.quests)
                self.draw_cursor(current, previous)
            elif c == 'p':
                previous = current
                current = (current - 1) % len(self.quests)
                self.draw_cursor(current, previous)
            elif c == 'c':
                result = rpg_mod.close_quest(self.db, self.cursor, self.quests[current]["id"])
                message = "Closed quest: " + result[0]
                if result[2]:
                    message = "Skill " + result[3] + " increased to level " + result[4]
                if result[1]:
                    message = "Hey! You leveled up!!!"
                self.print_message(message)
                redraw = True

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def draw_main(self):
        self.draw_list(
            self.quests,
            "|XP |Gold",
            "|{:<3}|{:<4}",
            ("xp", "gold"),
        )

    def draw_commands(self):
        self.draw_generic_commands([
            [("n", "next quest"), ("p", "previous quest"), ("", ""), ("", "")],
            [("c", "complete quest"), ("", ""), ("", ""), ("", "")],
            [("", ""), ("", ""), ("r", "return"), ("q", "quit")],
        ])


class AwardsListTab(ListTab):
    awards = []

    def open(self):
        navigation = {}
        current = 0
        redraw = True

        while True:
            if redraw:
                # retrieve the awards
                self.awards = rpg_mod.get_awards(self.cursor)

                current = 0
                self.draw_all()
                self.draw_cursor(0, 0)
                redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.clear_messages()

            # process the command
            if c == 'n':
                previous = current
                current = (current + 1) % len(self.awards)
                self.draw_cursor(current, previous)
            elif c == 'p':
                previous = current
                current = (current - 1) % len(self.awards)
                self.draw_cursor(current, previous)
            elif c == 'c':
                result = rpg_mod.claim_award(self.db, self.cursor, self.awards[current]["id"])
                self.print_message("{} costed you {} gold".format(result[0], result[1]))
                redraw = True

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def draw_main(self):
        self.draw_list(
            self.awards,
            "|Price",
            "|{:<5}",
            ("price",),
        )

    def draw_commands(self):
        self.draw_generic_commands([
            [("n", "next award"), ("p", "previous award"), ("", ""), ("", "")],
            [("c", "claim award"), ("", ""), ("", ""), ("", "")],
            [("", ""), ("", ""), ("r", "return"), ("q", "quit")],
        ])


class ProjectListTab(ListTab):
    projects = []
    current_project = 0

    def open(self):
        navigation = {
            "l": (TaskListInProjectTab, lambda: [self.projects[self.current_project]["id"]]),
        }
        redraw = True

        while True:
            if redraw:
                self.projects = project_mod.list_projects(self.cursor)

                self.draw_all()
                self.draw_cursor(0, 0)
                redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == 'n':
                previous = self.current_project
                self.current_project = (self.current_project + 1) % len(self.projects)
                self.draw_cursor(self.current_project, previous)
            elif c == 'p':
                previous = self.current_project
                self.current_project = (self.current_project - 1) % len(self.projects)
                self.draw_cursor(self.current_project, previous)
            elif c == 'l':
                # TODO: self.tasks_in_project(projects[current]["id"])
                pass
            elif c == 'e':
                self.print_message("Enter priority:")
                priority = self.get_input()
                if not priority:
                    self.print_message("Aborted")
                    continue
                project_mod.modify_project(self.db, self.cursor, self.projects[self.current_project]["id"],
                                           priority=priority)
                redraw = True
            elif c == 'a':
                self.print_message("Enter the name:")
                name = self.get_input()
                self.clear_messages()

                self.print_message("Enter priority (0 if left blank):")
                priority = self.get_input()
                priority = int(priority) if priority else 0
                self.clear_messages()

                project_mod.add_project(self.db, self.cursor, name, priority)
                redraw = True

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def draw_main(self):
        self.draw_list(
            self.projects,
            "|Priority",
            "|{:<8}",
            ("priority",),
        )

    def draw_commands(self):
        self.draw_generic_commands([
            [("n", "next project"), ("p", "previous project"), ("", ""), ("", "")],
            [("l", "list tasks"), ("e", "set priority"), ("a", "add project"), ("", "")],
            [("", ""), ("", ""), ("r", "return"), ("q", "quit")],
        ])


class ModifyTab(ListTab):
    tasks = []

    def open(self):
        self.tasks = self.call_stack.top_arguments()
        ids = [t["id"] for t in self.tasks]
        redraw = True

        while True:
            navigation = {}
            if redraw:
                self.draw_all()
                redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == 'n':
                self.print_message("Enter new name:")
                name = self.get_input()
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, name=name)
                    self.tasks[i]["name"] = name
                redraw = True
            elif c == 's':
                self.print_message("Enter new status, 0 - closed, 1 - open:")
                status = int(self.get_input())
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, status=status)
                    self.tasks[i]["status"] = status
                redraw = True
            elif c == 'p':
                self.print_message("Enter new priority:")
                priority = int(self.get_input())
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, priority=priority)
                    self.tasks[i]["priority"] = priority
                redraw = True
            elif c == 'w':
                self.print_message("Enter new weight:")
                weight = float(self.get_input())
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, weight=weight)
                    self.tasks[i]["weight"] = weight
                redraw = True
            elif c == 't':
                self.print_message("Enter new time (HH:MM):")
                time = self.get_input()
                if not core.validate_time(time):
                    self.print_message("Wrong time format. Aborted.")
                    continue

                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, time=time)
                    self.tasks[i]["time"] = time
                redraw = True
            elif c == 'a':
                self.print_message("Enter new due date (YYYY-MM-DD):")
                date = self.get_input()
                if not core.validate_relative_date(date):
                    self.print_message("Wrong date format. Aborted.")
                    continue

                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, due_date=date)
                    self.tasks[i]["due_date"] = date
                redraw = True
            elif c == 'e':
                self.print_message("Enter repetition period (no repetition if left blank):")
                repeat = self.get_input()
                if not core.validate_time_period(repeat):
                    self.print_message("Wrong period format. Aborted.")
                    continue

                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, repeat=repeat)
                    self.tasks[i]["repeat"] = repeat
                redraw = True
            elif c == 'd':
                if self.ask_confirmation("Do you want to delete the tasks?"):
                    for i in ids:
                        core.delete_task(self.db, self.cursor, i)
                    self.call_stack.pop()
                    return self.call_stack

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def draw_main(self):
        self.draw_list(
            self.tasks,
            "|ST|PR |WGHT|Time |Date      ",
            "|{:<2}|{:<3}|{:<1.2f}|{}|{}",
            ("status", "priority", "weight", "due_time", "due_date"),
        )

    def draw_commands(self):
        self.draw_generic_commands([
            [("n", "set name "), ("s", "set status"), ("p", "set priority"), ("w", "set weight")],
            [("t", "set due time"), ("a", "set due date"), ("e", "set repeat"), ("d", "delete tasks")],
            [("", ""), ("", ""), ("r", "return"), ("q", "quit")],
        ])


class TaskListInProjectTab(TaskListTab):
    project_id = None
    tasks = []
    current = 0

    def open(self):
        self.project_id = self.call_stack.top_arguments()[0]

        navigation = {
            "m": (ModifyTab, lambda: [self.tasks[self.current]]),
        }
        redraw = True
        include_overdue = True
        include_no_date = True

        # wait for commands
        while True:
            if redraw:
                self.tasks = core.list_tasks(self.cursor, project=self.project_id)
                if include_overdue:
                    self.tasks += core.list_tasks(self.cursor, project=self.project_id, list_overdue_tasks=True)
                if include_no_date:
                    self.tasks += core.list_tasks(self.cursor, project=self.project_id, due_date="no")
                self.current = 0

                self.draw_all()
                self.draw_cursor(0, 0)
                redraw = False

            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == 'n':
                previous = self.current
                self.current = (self.current + 1) % len(self.tasks)
                self.draw_cursor(self.current, previous)
            elif c == 'p':
                previous = self.current
                self.current = (self.current - 1) % len(self.tasks)
                self.draw_cursor(self.current, previous)
            elif c == 't':
                core.modify_task(self.db, self.cursor, self.tasks[self.current]["id"], due_date="today")
                redraw = True
            elif c == 'o':
                core.modify_task(self.db, self.cursor, self.tasks[self.current]["id"], due_date="no")
                redraw = True
            elif c == 'a':
                self.add_task(project=self.project_id, due_date="no", due_time=None)
                redraw = True
            elif c == 'h':
                task = self.tasks[self.current]
                core.modify_task(self.db, self.cursor, task["id"], priority=task["priority"] + 5)
                redraw = True
            elif c == 'l':
                task = self.tasks[self.current]
                new_priority = task["priority"] - 5 if task["priority"] >= 5 else 0
                core.modify_task(self.db, self.cursor, task["id"], priority=new_priority)
                redraw = True
            elif c == 'g':
                total, closed = project_mod.get_project_progress(self.cursor, self.project_id)
                self.print_message("Project progress: {} / {}".format(closed, total))

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def draw_commands(self):
        self.draw_generic_commands([
            [("n", "next"), ("p", "previous"), ("h", "higer prio."), ("l", "lower prio.")],
            [("t", "set for today"), ("o", "remove due date "), ("a", "add task"), ("m", "modify task")],
            [("g", "project progress"), ("", ""), ("r", "return"), ("q", "quit")],
        ])


def main(stdscr):
    # clear screen
    stdscr.clear()
    try:
        curses.curs_set(False)
    except curses.error:
        pass

    # connect to the DB
    config = core.read_configuration()
    database_file = config['db_path']
    db = sqlite3.connect(database_file)
    cursor = db.cursor()

    # prepare windows
    main_window = curses.newwin(30, curses.COLS - 1, 1, 0)
    message_window = curses.newwin(2, curses.COLS - 1, curses.LINES - 8, 0)
    commands_window = curses.newwin(5, curses.COLS - 1, curses.LINES - 6, 0)
    progress_window = curses.newwin(3, 25, curses.LINES - 1, 0)
    character_window = curses.newwin(3, 42, curses.LINES - 1, curses.COLS - 42)

    call_stack = CallStack()
    call_stack.push(HomeTab, [])

    while not call_stack.is_empty():
        CurrentTab = call_stack.top_tab()
        tab = CurrentTab(call_stack, db, cursor, stdscr,
                         main_window, message_window, commands_window, progress_window, character_window)
        call_stack = tab.open()


if __name__ == '__main__':
    curses.wrapper(main)
