import sublime, sublime_plugin
import os, os.path, subprocess, threading

# This file is heavily inspired on the Sublime standard distribution exec.py!

def find_parent_dir(pathish_haystack, dirnamish_needle):
  path = os.path.dirname(pathish_haystack)
  old = None
  max_recursions = 100
  while (old is not path and len(path) > 0):
    if (max_recursions <= 0 or os.path.basename(path) == dirnamish_needle):
      return path
    old = path
    path = os.path.dirname(path)
    max_recursions -= 1
  return None


class AppendBuildOutputCommand(sublime_plugin.TextCommand):
  def run(self, edit, data, follow_output):
    self.view.insert(edit, self.view.size(), data)
    if follow_output:
      self.view.show(self.view.size())


class GenericRunnerThread(threading.Thread):
  def __init__(self, cmd, working_dir=None, env=None, silent=False, shell=False, view=None):
    self.startup_info = None
    if (os.name is 'nt'):
      self.startup_info = subprocess.STARTUPINFO()
      self.startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    self.cmd = cmd
    self.working_dir = working_dir
    self.env = os.environ.copy()
    self.silent = silent
    self.shell = shell
    self.output_view = view
    if (env is not None):
      self.env.update(env)
    threading.Thread.__init__(self)

  def log_output(self, output):
    if (output is None):
      return
    data = output.decode("UTF-8")
    data = data.replace('\r\n', '\n').replace('\r', '\n')
    if (self.output_view):
      follow_output = len(self.output_view.sel()) == 1 and self.output_view.sel()[0] == sublime.Region(self.output_view.size())
      self.output_view.set_read_only(False)
      self.output_view.run_command("append_build_output", {"data": data, "follow_output": follow_output})
      self.output_view.set_read_only(True)

  def run(self):
    worker = subprocess.Popen(args=self.cmd,
                              cwd=self.working_dir,
                              env=self.env,
                              shell=self.shell,
                              startupinfo=self.startup_info,
                              stdout=(None if self.silent else subprocess.PIPE),
                              stderr=(None if self.silent else subprocess.PIPE))
    output, error = worker.communicate()
    if (error and not self.silent):
      self.log_output(output)
    if (output and not self.silent):
      self.log_output(output)


class CucumberFrontendThread(GenericRunnerThread):
  def __init__(self, cucumber, feature_dir, shell, view):
    GenericRunnerThread.__init__(self,
                                 cmd=[ cucumber, feature_dir ],
                                 working_dir=feature_dir,
                                 env={},
                                 shell=shell,
                                 view=view)


class CukeWiredRunnerThread(GenericRunnerThread):
  def __init__(self, runner, runner_env, shell, view):
    GenericRunnerThread.__init__(self,
                                 cmd=[ runner ],
                                 env=runner_env,
                                 silent=True,
                                 shell=shell,
                                 view=view)


class CukeTestwalkerCommand(sublime_plugin.WindowCommand):
  def automagically_locate(self, dir_name):
    try:
      viewed_file = self.window.active_view().file_name()
      return find_parent_dir(viewed_file, dir_name)
    except Exception as error:
      return None

  def is_enabled(self):
    return True

  def run(self, **args):
    self.feature_dir = args.get('feature_dir', self.automagically_locate("features"))
    self.cucumber = args.get('cucumber', 'cucumber')
    self.cucumber_needs_shell = args.get('cucumber_needs_shell', False)
    self.runner = args.get('runner', None)
    self.runner_env = args.get('runner_env', None)
    self.runner_needs_shell = args.get('runner_needs_shell', False)

    if (self.feature_dir is None):
      raise ValueError('Argument `feature_dir` needs to be the path to a Gherkin `features` directory!')

    cucumber_working_dir = os.path.dirname(self.feature_dir)
    self.output_view = self.window.create_output_panel("exec")
    self.output_view.settings().set("result_base_dir", cucumber_working_dir)
    self.window.run_command("show_panel", {"panel": "output.exec"})

    if (self.runner is not None):
      runner_thread = CukeWiredRunnerThread(self.runner,
                                            self.runner_env,
                                            self.runner_needs_shell,
                                            self.output_view)
      runner_thread.start()

    frontend_thread = CucumberFrontendThread(self.cucumber,
                                             cucumber_working_dir,
                                             self.cucumber_needs_shell,
                                             self.output_view)
    frontend_thread.start()
