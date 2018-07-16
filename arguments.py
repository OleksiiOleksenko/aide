import datetime
import re
from argparse import ArgumentParser, ArgumentTypeError


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
        default="00:00",
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
        type=validate_repeat_period,
        help="Repetition period. Format examples: "
        "'1 years' "
        "'12 months' "
        "'123 days' "
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
        default="",
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
        type=validate_repeat_period,
        help="Repetition period. Format examples: "
        "'1 years' "
        "'12 months' "
        "'123 days' "
    )

    # closing tasks
    parser_close = subparsers.add_parser('close', help='Mark a task as closed')
    parser_close.add_argument(
        'id',
        type=str,
        help="ID of the task to close"
    )

    # deleting tasks
    parser_delete = subparsers.add_parser('delete', help='Permanently delete a task')
    parser_delete.add_argument(
        'id',
        type=str,
        help="ID of the task to delete"
    )

    # total weight
    parser_total = subparsers.add_parser('total',
                                         help='Calculate a total weight of tasks. '
                                              'If no arguments specified - '
                                              'weight of all tasks today (both open and closed)')
    parser_total.add_argument(
        '-d', '--date',
        type=str,
        help="Total weight of tasks on a given date. Date format: YYYY-MM-DD"
    )
    parser_total.add_argument(
        '-o', '--open',
        action='store_true',
        help="Total weight of open tasks today"
    )

    args = parser.parse_args()
    return args


def validate_time(time_string: str):
    try:
        datetime.datetime.strptime(time_string, "%H:%M")
    except ValueError:
        raise ArgumentTypeError("Incorrect time format, should be HH:MM")
    return time_string


def validate_repeat_period(date_string: str):
    pattern = r"\d{1,3} (days|months|years)"
    result = re.search(pattern, date_string)

    if not result:
        raise ArgumentTypeError("Incorrect time format, should match " + pattern)
    return date_string
