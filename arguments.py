from argparse import ArgumentParser


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
        help='Verbosity level: defines how much information to show.'
             '(-v 1 - [default] basic info;'
             '-v 2 - not implemented;'
             '-v 3 - full experiment description, including HW parameters, compilers and flags, etc.)'
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        required=False,
        help='Debug mode: compile with debug info (but still with all optimizations enabled) and set helpful environmental variables.'
    )

    # adding tasks
    parser_add = subparsers.add_parser('add', help='download and install all benchmarks')
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
        type=str,
        default="00:00",
        help="Start time of the task. Format: -t HH:MM"
    )
    parser_add.add_argument(
        '-w', '--weight',
        type=float,
        default=0,
        help="tbd"
    )

    # listing tasks
    parser_list = subparsers.add_parser('list', help='download and install all benchmarks')
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
    parser_mod = subparsers.add_parser('mod', help='download and install all benchmarks')
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
        type=str,
        default="",
        help="Start time of the task. Format HH:MM"
    )
    parser_mod.add_argument(
        '-w', '--weight',
        type=float,
        default=-1,
        help="tbd"
    )

    # closing tasks
    parser_close = subparsers.add_parser('close', help='download and install all benchmarks')
    parser_close.add_argument(
        'id',
        type=str,
        help="ID of the task to close"
    )

    # deleting tasks
    parser_delete = subparsers.add_parser('delete', help='download and install all benchmarks')
    parser_delete.add_argument(
        'id',
        type=str,
        help="ID of the task to delete"
    )

    # initializing a day
    parser_init = subparsers.add_parser('init', help='download and install all benchmarks')

    # total weight
    parser_total = subparsers.add_parser('total', help='download and install all benchmarks')
    parser_total.add_argument(
        '-d', '--date',
        type=str,
        help="List open tasks at a given date. Format: YYYY-MM-DD"
    )
    parser_total.add_argument(
        '-o', '--open',
        action='store_true',
        help="List open tasks"
    )

    args = parser.parse_args()
    return args
