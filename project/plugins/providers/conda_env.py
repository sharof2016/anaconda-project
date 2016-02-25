"""Conda environment providers."""
from __future__ import absolute_import, print_function

import os

import project.internal.conda_api as conda_api
from project.plugins.provider import Provider


class ProjectScopedCondaEnvProvider(Provider):
    """Provides a project-scoped Conda environment."""

    @property
    def title(self):
        """Override superclass to provide our title."""
        return "Conda environment inside the project directory"

    def read_config(self, context):
        """Override superclass to return empty config."""
        return dict()

    def provide(self, requirement, context):
        """Override superclass to activating a project-scoped environment (creating it if needed)."""
        # TODO: we are ignoring any version or build specs for the package names.
        # the hard part about this is that the conda command line which we use
        # to create the environment has a different syntax from meta.yaml which we
        # use to create the required package specs, so we can't just pass the meta.yaml
        # syntax to the conda command line.
        command_line_packages = set(['python']).union(requirement.conda_package_names_set)

        # future: we could use environment.yml if present to create the default env
        prefix = os.path.join(context.environ['PROJECT_DIR'], ".envs", "default")
        try:
            conda_api.create(prefix=prefix, pkgs=list(command_line_packages))
        except conda_api.CondaEnvExistsError:
            pass
        except conda_api.CondaError as e:
            context.append_error(str(e))
            prefix = None

        if prefix is not None:
            # now install any missing packages (should only happen if env didn't exist,
            # otherwise we passed the needed packages to create)
            installed = conda_api.installed(prefix)
            missing = set()
            for name in command_line_packages:
                if name not in installed:
                    missing.add(name)
            if len(missing) > 0:
                try:
                    conda_api.install(prefix=prefix, pkgs=list(missing))
                except conda_api.CondaError as e:
                    context.append_error("Failed to install missing packages: " + ", ".join(missing))
                    context.append_error(str(e))
                    prefix = None

        if prefix is not None:
            context.environ[requirement.env_var] = prefix
            path = context.environ.get("PATH", "")
            context.environ["PATH"] = conda_api.set_conda_env_in_path(path, prefix)
            # Some stuff can only be done when a shell is launched:
            #  - we can't set PS1 because it shouldn't be exported.
            #  - we can't run conda activate scripts because they are sourced.
            # We can do these in the output of our activate command, but not here.