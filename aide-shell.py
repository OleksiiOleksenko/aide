#!/usr/bin/env python3
import curses
import curses.ascii
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
    redraw: bool = True

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

    def resize(self):
        lines, cols = self.stdscr.getmaxyx()
        self.stdscr.clear()
        self.main_window = curses.newwin(30, cols - 1, 1, 0)
        self.message_window = curses.newwin(3, cols - 1, lines - 9, 0)
        self.commands_window = curses.newwin(5, cols - 1, lines - 6, 0)
        self.progress_window = curses.newwin(3, 25, lines - 1, 0)
        self.character_window = curses.newwin(3, 42, lines - 1, cols - 42)
        self.stdscr.refresh()

    def print_message(self, text: str):
        self.message_window.addstr(0, 1, text)
        self.stdscr.refresh()
        self.message_window.refresh()

    def print_help(self, text: str):
        self.message_window.addstr(1, 1, text)
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

    def get_input(self, default: str = "") -> (str, str):
        self.message_window.move(2, 1)

        s = ""
        status = "ok"
        while True:
            self.message_window.deleteln()
            self.message_window.addstr(2, 1, ">> " + s)
            self.message_window.refresh()
            self.stdscr.refresh()

            c = self.message_window.getch()
            if c == 27:
                status = "cancel"
                break

            if c == curses.ascii.ACK:  # ^f
                status = "finish"
                break

            if c == curses.KEY_ENTER or c == 10 or c == 13:  # Enter
                break

            if c == curses.KEY_BACKSPACE or c == 127 or c == curses.KEY_DC:
                s = s[:-1]
                continue

            s += chr(c)

        if not s:
            s = default

        return s, status

    def add_task(self, project: int = 1):
        params = [
            ["", "Enter the task", lambda x: True, str],
            [0.0, "Enter task weight (0.0 if left blank)", lambda x: True, float],
            [0, "Enter task priority (0 if left blank)", lambda x: True, int],
            ["", "Enter due date (YYYY-MM-DD) (today if left blank)", core.validate_relative_date, str],
            ["", "Enter due time (HH:MM) (00:00 if left blank)", core.validate_time, str],
            ["", "Enter repetition period (no repetition if left blank)", core.validate_time_period, str],
            [project, "Enter project", lambda x: True, int],
            [None, "Enter related quest", lambda x: True, int],
        ]

        for i, p in enumerate(params):
            self.print_message(p[1] + ":")
            text, status = self.get_input(p[0])
            if status == "cancel":
                return
            if status == "finish":
                break
            if not p[2](text):
                self.print_message("Wrong format. Aborted.")
                return
            params[i][0] = p[3](text)
            self.message_window.clear()

        core.add_task(self.db, self.cursor, params[0][0], params[2][0], params[4][0], params[3][0], params[1][0],
                      params[5][0], params[6][0], params[7][0])
        return

    def process_navigation_commands(self, command: str, navigation: dict, enable_return: bool = True):
        # handle resizing
        if command == "KEY_RESIZE":
            self.resize()
            self.redraw = True
            return False

        # quit
        if command == 'q':
            self.call_stack.clear()
            return True

        # return to previous window
        if enable_return and command == 'r':
            self.call_stack.pop()
            return True

        if navigation.get(command, None):
            next_tab = navigation[command][0]
            arguments = navigation[command][1]()  # pre-call and get arguments
            self.call_stack.push(next_tab, arguments)
            return True

        return False


class ListTab(Tab):
    priority_step = 10

    def draw_list(self, list_, columns_header: str, column_format: str, column_fields):
        self.main_window.erase()

        # table header
        self.main_window.addstr(1, 1, "Name")
        if columns_header:
            self.main_window.addstr(1, curses.COLS - len(columns_header) - 1, columns_header)
        self.main_window.hline(2, 0, curses.ACS_HLINE, curses.COLS - 1)

        # list
        line = 3
        for element in list_:
            self.main_window.addstr(line, 2, element["name"])
            if column_fields:
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


class DialogTab(Tab):
    pass


class HomeTab(Tab):
    task = None

    def open(self):
        navigation = {
            "l": (TaskListTab, lambda: [0]),
            "u": (QuestsListTab, lambda: []),
            "w": (AwardsListTab, lambda: []),
            "p": (ProjectListTab, lambda: []),
            "m": (ModifyTab, lambda: [self.task] if self.task else []),
            "s": (ReportTab, lambda: []),
            "n": (AddNoteTab, lambda: []),
        }

        while True:
            if self.redraw:
                # retrieve the current task and update windows
                self.task = core.list_tasks(self.cursor, True)
                self.task = self.task[0] if self.task else None
                self.draw_all()
                self.redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process normal command
            if c == 'a':
                self.add_task()
                self.redraw = True
            elif c == 'c':
                if not self.task:
                    self.print_message("No task to close")
                    continue

                if self.ask_confirmation("Do you want to close the current task?"):
                    core.close_task(self.db, self.cursor, self.task["id"])
                    self.redraw = True
            elif c == "KEY_DC":
                if not self.task:
                    self.print_message("No task to delete")
                    continue

                if self.ask_confirmation("Do you want to delete the current task?"):
                    core.delete_task(self.db, self.cursor, self.task["id"])
                    self.redraw = True

            if self.process_navigation_commands(c, navigation, enable_return=False):
                return self.call_stack

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
            [("a", "add task"), ("m", "modify current"), ("c", "close current"), ("", "DEL: delete current")],
            [("l", "list tasks"), ("n", "add note"), ("s", "show reports"), ("p", "projects")],
            [("u", "quests"), ("w", "awards"), ("", ""), ("q", "quit")],
        ])


class TaskListTab(ListTab):
    tasks = []
    selected_tasks = set()
    current = 0

    def open(self):
        self.current = self.call_stack.top_arguments()[0]

        navigation = {
            "m": (ModifyTab, self.call_modify)
        }
        include_overdue = True
        include_closed = False

        while True:
            if self.redraw:
                if include_closed:
                    self.tasks = core.list_tasks(self.cursor, False, exclude_closed_tasks=False)
                else:
                    self.tasks = core.list_tasks(self.cursor, False, exclude_closed_tasks=True)
                if include_overdue:
                    self.tasks += core.list_tasks(self.cursor, False, list_overdue_tasks=True)
                if not self.tasks:
                    self.print_message("No open tasks!")

                # self.current = 0
                self.selected_tasks.clear()

                self.draw_all()
                self.draw_cursor(self.current, 0)
                self.redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == "j":
                previous = self.current
                self.current = (self.current + 1) % len(self.tasks)
                self.draw_cursor(self.current, previous)
            elif c == "k":
                previous = self.current
                self.current = (self.current - 1) % len(self.tasks)
                self.draw_cursor(self.current, previous)
            elif c == 's':
                self.selected_tasks.add(self.current)
                self.draw_selection(self.current)
            elif c == 'u':
                self.selected_tasks.discard(self.current)
                self.draw_selection(self.current, True)
            elif c == 'o':
                include_overdue = False
                self.redraw = True
            elif c == 'c':
                include_closed = True
                self.redraw = True
            elif c == 'a':
                self.add_task()
                self.redraw = True
            elif c == 'p':
                task = self.tasks[self.current]
                new_priority = task["priority"] + self.priority_step
                core.modify_task(self.db, self.cursor, task["id"], priority=new_priority)
                self.redraw = True
            elif c == 'P':
                task = self.tasks[self.current]
                new_priority = task["priority"] - self.priority_step if task["priority"] >= self.priority_step else 0
                core.modify_task(self.db, self.cursor, task["id"], priority=new_priority)
                self.redraw = True

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
            [("j", "next task"), ("k", "previous task"), ("s", "select "), ("u", "undo selection")],
            [("a", "add task"), ("m", "modify selected"), ("p", "increase prio."), ("P", "decrease prio.")],
            [("o", "exclude overdue"), ("c", "include closed"), ("r", "return"), ("q", "quit")],
        ])

    def call_modify(self):
        self.call_stack.top_arguments()[0] = self.current
        if self.selected_tasks:
            task_list = [self.tasks[i] for i in self.selected_tasks]
        else:
            task_list = [self.tasks[self.current]]
        return task_list


class QuestsListTab(ListTab):
    quests = []

    def open(self):
        navigation = {}
        current = 0
        self.redraw = True

        while True:
            if self.redraw:
                # retrieve the quests
                self.quests = rpg_mod.get_quests(self.cursor)

                current = 0
                self.draw_all()
                self.draw_cursor(0, 0)
                self.redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == "j":
                previous = current
                current = (current + 1) % len(self.quests)
                self.draw_cursor(current, previous)
            elif c == "k":
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
                self.redraw = True
            elif c == 'a':
                self.add_quest()
                self.redraw = True

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
            [("j", "next quest"), ("k", "previous quest"), ("", ""), ("", "")],
            [("c", "complete quest"), ("a", "new quest"), ("", ""), ("", "")],
            [("", ""), ("", ""), ("r", "return"), ("q", "quit")],
        ])

    def add_quest(self):
        self.print_message("Enter the quest name:")
        name, status = self.get_input()
        if status == "cancel":
            return
        self.message_window.clear()

        self.print_message("Enter the awarded xp (0 if left blank):")
        xp, status = self.get_input()
        if status == "cancel":
            return
        xp = int(xp) if xp else 0
        self.message_window.clear()

        self.print_message("Enter the gold reward (0 if left blank):")
        gold, status = self.get_input()
        if status == "cancel":
            return
        gold = int(gold) if gold else 0
        self.message_window.clear()

        skills = rpg_mod.get_skills(self.cursor)
        skill_list = ", ".join([str(s["id"]) + ": " + s["name"] for s in skills])
        self.print_help("Available: " + skill_list)
        self.print_message("Enter the trained skill id:")
        skill, status = self.get_input()
        if status == "cancel":
            return
        if skill is None:
            return
        skill = int(skill) if skill else 0
        self.message_window.clear()

        rpg_mod.add_quest(self.db, self.cursor, name, xp, gold, skill)
        return True


class AwardsListTab(ListTab):
    awards = []

    def open(self):
        navigation = {}
        current = 0
        self.redraw = True

        while True:
            if self.redraw:
                # retrieve the awards
                self.awards = rpg_mod.get_awards(self.cursor)

                current = 0
                self.draw_all()
                self.draw_cursor(0, 0)
                self.redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.clear_messages()

            # process the command
            if c == "j":
                previous = current
                current = (current + 1) % len(self.awards)
                self.draw_cursor(current, previous)
            elif c == "k":
                previous = current
                current = (current - 1) % len(self.awards)
                self.draw_cursor(current, previous)
            elif c == 'c':
                result = rpg_mod.claim_award(self.db, self.cursor, self.awards[current]["id"])
                self.print_message("{} costed you {} gold".format(result[0], result[1]))
                self.redraw = True
            elif c == 'a':
                self.add_award()
                self.redraw = True

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def add_award(self):
        self.print_message("Enter the award name:")
        name, status = self.get_input()
        if status == "cancel":
            return
        if name is None:
            return
        self.message_window.clear()

        self.print_message("Enter the award price (0 if left blank):")
        price, status = self.get_input()
        if status == "cancel":
            return
        if price is None:
            return
        price = int(price) if price else 0
        self.message_window.clear()

        rpg_mod.add_award(self.db, self.cursor, name, price)
        return True

    def draw_main(self):
        self.draw_list(
            self.awards,
            "|Price",
            "|{:<5}",
            ("price",),
        )

    def draw_commands(self):
        self.draw_generic_commands([
            [("j", "next award"), ("k", "previous award"), ("", ""), ("", "")],
            [("c", "claim award"), ("a", "new award"), ("", ""), ("", "")],
            [("", ""), ("", ""), ("r", "return"), ("q", "quit")],
        ])


class ProjectListTab(ListTab):
    projects = []
    current_project = 0

    def open(self):
        navigation = {
            "l": (TaskListInProjectTab, lambda: [self.projects[self.current_project]["id"], 0]),
        }
        self.redraw = True

        while True:
            if self.redraw:
                self.projects = project_mod.list_projects(self.cursor)

                self.draw_all()
                self.draw_cursor(0, 0)
                self.redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == "j":
                previous = self.current_project
                self.current_project = (self.current_project + 1) % len(self.projects)
                self.draw_cursor(self.current_project, previous)
            elif c == "k":
                previous = self.current_project
                self.current_project = (self.current_project - 1) % len(self.projects)
                self.draw_cursor(self.current_project, previous)
            elif c == 'e':
                self.print_message("Enter priority:")
                priority, status = self.get_input()
                if status == "cancel":
                    self.print_message("Aborted")
                    continue
                priority = int(priority)
                project_mod.modify_project(self.db, self.cursor, self.projects[self.current_project]["id"],
                                           priority=priority)
                self.redraw = True
            elif c == 'a':
                self.add_project()
                self.redraw = True

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def add_project(self):
        self.print_message("Enter the name:")
        name, status = self.get_input()
        if status == "cancel":
            return
        self.clear_messages()

        self.print_message("Enter priority (0 if left blank):")
        priority, status = self.get_input()
        if status == "cancel":
            return
        priority = int(priority) if priority else 0
        self.clear_messages()

        project_mod.add_project(self.db, self.cursor, name, priority)

    def draw_main(self):
        self.draw_list(
            self.projects,
            "|Priority",
            "|{:<8}",
            ("priority",),
        )

    def draw_commands(self):
        self.draw_generic_commands([
            [("j", "next project"), ("k", "previous project"), ("", ""), ("", "")],
            [("l", "list tasks"), ("e", "set priority"), ("a", "add project"), ("", "")],
            [("", ""), ("", ""), ("r", "return"), ("q", "quit")],
        ])


class ModifyTab(ListTab):
    tasks = []

    def open(self):
        self.tasks = self.call_stack.top_arguments()
        ids = [t["id"] for t in self.tasks]
        self.redraw = True

        while True:
            navigation = {}
            if self.redraw:
                self.draw_all()
                self.redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == 'n':
                self.print_message("Enter new name:")
                name, status = self.get_input()
                if status == "cancel":
                    continue
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, name=name)
                    self.tasks[i]["name"] = name
                self.redraw = True
            elif c == 's':
                self.print_message("Enter new status, 0 - closed, 1 - open:")
                st, status = self.get_input()
                if status == "cancel":
                    continue
                st = int(st)
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, status=st)
                    self.tasks[i]["status"] = status
                self.redraw = True
            elif c == 'p':
                self.print_message("Enter new priority:")
                priority, status = self.get_input()
                if status == "cancel":
                    continue
                priority = int(priority)
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, priority=priority)
                    self.tasks[i]["priority"] = priority
                self.redraw = True
            elif c == 'w':
                self.print_message("Enter new weight:")
                weight, status = self.get_input()
                if status == "cancel":
                    continue
                weight = float(weight)
                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, weight=weight)
                    self.tasks[i]["weight"] = weight
                self.redraw = True
            elif c == 't':
                self.print_message("Enter new time (HH:MM):")
                time, status = self.get_input()
                if status == "cancel":
                    continue
                if not core.validate_time(time):
                    self.print_message("Wrong time format. Aborted.")
                    continue

                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, time=time)
                    self.tasks[i]["time"] = time
                self.redraw = True
            elif c == 'd':
                self.print_message("Enter new due date (YYYY-MM-DD):")
                date, status = self.get_input()
                if status == "cancel":
                    continue
                if not core.validate_relative_date(date):
                    self.print_message("Wrong date format. Aborted.")
                    continue

                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, due_date=date)
                    self.tasks[i]["due_date"] = date
                self.redraw = True
            elif c == 'e':
                self.print_message("Enter repetition period (no repetition if left blank):")
                repeat, status = self.get_input()
                if status == "cancel":
                    continue
                if not core.validate_time_period(repeat):
                    self.print_message("Wrong period format. Aborted.")
                    continue

                for i, id_ in enumerate(ids):
                    core.modify_task(self.db, self.cursor, id_=id_, repeat=repeat)
                    self.tasks[i]["repeat"] = repeat
                self.redraw = True
            elif c == "KEY_DC":
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
            [("t", "set due time"), ("d", "set due date"), ("e", "set repeat"), ("", "DEL: delete tasks")],
            [("", ""), ("", ""), ("r", "return"), ("q", "quit")],
        ])


class TaskListInProjectTab(TaskListTab):
    project_id = None

    def open(self):
        self.project_id = self.call_stack.top_arguments()[0]
        self.current = self.call_stack.top_arguments()[1]

        navigation = {
            "m": (ModifyTab, self.call_modify),
        }
        self.redraw = True
        include_overdue = True
        include_no_date = True

        # wait for commands
        while True:
            if self.redraw:
                self.tasks = core.list_tasks(self.cursor, project=self.project_id)
                if include_overdue:
                    self.tasks += core.list_tasks(self.cursor, project=self.project_id, list_overdue_tasks=True)
                if include_no_date:
                    self.tasks += core.list_tasks(self.cursor, project=self.project_id, due_date="no")
                # self.current = 0

                self.draw_all()
                self.draw_cursor(self.current, 0)
                self.redraw = False

            c = self.stdscr.getkey()
            self.message_window.clear()

            # process the command
            if c == "j":
                previous = self.current
                self.current = (self.current + 1) % len(self.tasks)
                self.draw_cursor(self.current, previous)
            elif c == "k":
                previous = self.current
                self.current = (self.current - 1) % len(self.tasks)
                self.draw_cursor(self.current, previous)
            elif c == 't':
                core.modify_task(self.db, self.cursor, self.tasks[self.current]["id"], due_date="today")
                self.redraw = True
            elif c == 'n':
                core.modify_task(self.db, self.cursor, self.tasks[self.current]["id"], due_date="no")
                self.redraw = True
            elif c == 'a':
                self.add_task(project=self.project_id)
                self.redraw = True
            elif c == 'p':
                task = self.tasks[self.current]
                core.modify_task(self.db, self.cursor, task["id"], priority=task["priority"] + self.priority_step)
                self.redraw = True
            elif c == 'P':
                task = self.tasks[self.current]
                new_priority = task["priority"] - self.priority_step if task["priority"] >= self.priority_step else 0
                core.modify_task(self.db, self.cursor, task["id"], priority=new_priority)
                self.redraw = True
            elif c == 'g':
                total, closed = project_mod.get_project_progress(self.cursor, self.project_id)
                self.print_message("Project progress: {} / {}".format(closed, total))

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def draw_commands(self):
        self.draw_generic_commands([
            [("j", "next"), ("k", "previous"), ("p", "higer prio."), ("P", "lower prio.")],
            [("t", "set for today"), ("n", "remove due date "), ("a", "add task"), ("m", "modify task")],
            [("g", "project progress"), ("", ""), ("r", "return"), ("q", "quit")],
        ])

    def call_modify(self):
        self.call_stack.top_arguments()[1] = self.current
        return [self.tasks[self.current]]


class ReportTab(ListTab):
    projects = []
    current = 0

    def open(self):
        navigation = {}
        self.projects = project_mod.list_projects(self.cursor)
        self.projects.append({"name": "All", "id": None})
        self.redraw = True

        while True:
            if self.redraw:
                self.draw_all()
                self.draw_cursor(self.current, 0)
                self.redraw = False

            # wait for commands
            c = self.stdscr.getkey()
            self.message_window.clear()

            if c == "j":
                previous = self.current
                self.current = (self.current + 1) % len(self.projects)
                self.draw_cursor(self.current, previous)
            elif c == "k":
                previous = self.current
                self.current = (self.current - 1) % len(self.projects)
                self.draw_cursor(self.current, previous)
            elif c == 'd':
                status = core.productivity_plot(self.cursor, [self.projects[self.current]["id"]])
                if not status:
                    self.print_message("Not enough data to build a plot!")

            if self.process_navigation_commands(c, navigation):
                return self.call_stack

    def draw_main(self):
        self.draw_list(self.projects, "", "", [])

    def draw_commands(self):
        self.draw_generic_commands([
            [("j", "next project"), ("k", "previous project"), ("", ""), ("", "")],
            [("d", "draw plot"), ("", ""), ("", ""), ("", "")],
            [("", ""), ("", ""), ("r", "return"), ("q", "quit")],
        ])


class AddNoteTab(DialogTab):
    def open(self):
        self.draw_all()

        params = [
            ["", "Enter the note", lambda x: True, str],
            ["today", "Enter the date (YYYY-MM-DD) (today if left blank)", core.validate_relative_date, str],
        ]

        for i, p in enumerate(params):
            self.print_message(p[1] + ":")
            text, status = self.get_input(p[0])
            if status == "cancel":
                return
            if status == "finish":
                break
            if not p[2](text):
                self.print_message("Wrong format. Aborted.")
                return
            params[i][0] = p[3](text) if text else p[0]
            self.message_window.clear()

        core.add_note(self.db, self.cursor, params[1][0], params[0][0])

        self.call_stack.pop()
        return self.call_stack

    def draw_main(self):
        self.main_window.erase()
        self.main_window.refresh()
        self.stdscr.refresh()

    def draw_commands(self):
        self.draw_generic_commands([
            [("j", "next selection"), ("k", "prev. selection (selections may not be available)"), ("", ""), ("", "")],
            [("", ""), ("", ""), ("", ""), ("", "")],
            [("", "^F: leave the rest of the fields on defaults"), ("", ""), ("", ""), ("", "ESC: cancel")],
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
    message_window = curses.newwin(3, curses.COLS - 1, curses.LINES - 9, 0)
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
