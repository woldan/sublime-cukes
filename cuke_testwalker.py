import sublime, sublime_plugin
import os, os.path, subprocess, threading

def find_parent_dir(pathish_haystack, dirnamish_needle):
  path = os.path.dirname(pathish_haystack)
  old = None
  while (old is not path and len(path) > 0):
    if (os.path.basename(path) == dirnamish_needle):
      return path
    old = path
    path = os.path.dirname(path)
  return None


class GenericRunnerThread(threading.Thread):
  def __init__(self, cmd, working_dir=None, env=None, silent=False, shell=False):
    self.startup_info = None
    if (os.name is 'nt'):
      self.startup_info = subprocess.STARTUPINFO()
      self.startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    self.cmd = cmd
    self.working_dir = working_dir
    self.env = os.environ.copy()
    self.silent = silent
    self.shell = shell
    if (env is not None):
      self.env.update(env)
    threading.Thread.__init__(self)

  def log_output(self, output):
    print("LOG = '{0}'".format(output))
    if (output is None):
      return
    data = output.decode("UTF-8")
    data = data.replace('\r\n', '\n').replace('\r', '\n')
    print(data)

  def run(self):
    worker = subprocess.Popen(args=self.cmd,
                              cwd=self.working_dir,
                              env=self.env,
                              shell=self.shell,
                              startupinfo=self.startup_info,
                              stdout=(None if self.silent else subprocess.PIPE),
                              stderr=(None if self.silent else subprocess.PIPE))
    output, error = worker.communicate()
    self.log_output(output)


class CucumberFrontendThread(GenericRunnerThread):
  def __init__(self, cucumber, feature_dir, shell):
    GenericRunnerThread.__init__(self,
                                 cmd=[ cucumber, feature_dir ],
                                 working_dir=feature_dir,
                                 env={},
                                 shell=shell)


class CukeWiredRunnerThread(GenericRunnerThread):
  def __init__(self, runner, runner_env, shell):
    GenericRunnerThread.__init__(self,
                                 cmd=[ runner ],
                                 env=runner_env,
                                 silent=True,
                                 shell=shell)


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

    if (self.runner is not None):
      runner_thread = CukeWiredRunnerThread(self.runner,
                                            self.runner_env,
                                            self.runner_needs_shell)
      runner_thread.start()

    frontend_thread = CucumberFrontendThread(self.cucumber,
                                             os.path.dirname(self.feature_dir),
                                             self.cucumber_needs_shell)
    frontend_thread.start()
