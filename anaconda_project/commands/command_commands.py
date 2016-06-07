# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2016, Continuum Analytics, Inc. All rights reserved.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# ----------------------------------------------------------------------------
"""Commands related to the 'commands' section of project.yml."""
from __future__ import absolute_import, print_function

import os
import platform
import sys

from anaconda_project.project import Project
from anaconda_project import project_ops
from anaconda_project.commands import console_utils


def _ask_command(command):
    if not console_utils.stdin_is_interactive():
        return None

    if platform.system() == 'Windows':
        other = 'windows'
    else:
        other = 'unix'
    choices = {'b': 'bokeh_app', 'c': other, 'n': 'notebook'}

    while True:
        data = console_utils.console_input("Is `{}` a (B)okeh app, (N)otebook, or (C)ommand line? ".format(command))
        data = data.lower().strip()

        if len(data) == 0 or data[0] not in choices:
            print("Please enter 'b', 'n', or 'c'.")
            print("    A Bokeh app is the project-relative path to a Bokeh script or app directory.")
            print("    A notebook file is the project-relative path to a .ipynb file.")
            print("    A command line is any command you might type at the command prompt.")
            continue

        return choices[data]


def add_command(project_dir, name, command_type, command, env_spec_name):
    """Add command to project.yml.

    Returns:
        int exit code
    """
    project = Project(project_dir)

    command_as_filename = os.path.join(project.directory_path, command)

    if command_type is None and command.endswith(".ipynb") and os.path.isfile(command_as_filename):
        command_type = 'notebook'

    if command_type is None or command_type == 'ask':
        command_type = _ask_command(name)

    if command_type is None:  # EOF, probably not an interactive console
        print("Specify the --type option to add this command.", file=sys.stderr)
        return 1

    status = project_ops.add_command(project, name, command_type, command, env_spec_name)
    if not status:
        console_utils.print_status_errors(status)
        return 1
    else:
        print("Added a command '%s' to the project. Run it with `anaconda-project run --command %s`." % (name, name))
        return 0


def remove_command(project_dir, name):
    """Remove a command from the project.

    Returns:
        int exit code
    """
    project = Project(project_dir)

    status = project_ops.remove_command(project, name)
    if not status:
        console_utils.print_status_errors(status)
        return 1
    else:
        print("Removed the command '{}' from the project.".format(name))
        return 0


def list_commands(project_dir):
    """List the commands on the project.

    Returns:
        int exit code
    """
    project = Project(project_dir)
    if console_utils.print_project_problems(project):
        return 1

    if project.commands:
        print("Commands for project: {}\n".format(project_dir))
        console_utils.print_names_and_descriptions(project.commands.values())
    else:
        print("No commands found for project: {}\n".format(project_dir))
    return 0


def main(args):
    """Submit the add command with args and returns exit code."""
    return add_command(args.project, args.name, args.type, args.command, args.env_spec)


def main_remove(args):
    """Submit the remove command with args and returns exit code."""
    return remove_command(args.project, args.name)


def main_list(args):
    """Start the list command with args and return exit code."""
    return list_commands(args.project)
