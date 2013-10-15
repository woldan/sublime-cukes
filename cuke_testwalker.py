import sublime, sublime_plugin
import os, os.path, subprocess, threading

def find_parent_dir(pathish_haystack, dirnamish_needle):
  path = os.path.dirname(pathish_haystack)
  while (len(path) > 0):
    if (os.path.basename(path) == dirnamish_needle):
      return path
    path = os.path.dirname(path)
  return None


class GenericRunnerThread(threading.Thread):
  def __init__(self, cmd, env=None, silent=False):
    self.startup_info = subprocess.STARTUPINFO()
    self.startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    self.cmd = cmd
    self.env = os.environ.copy()
    self.silent = silent
    if (env is not None):
      self.env.update(env)
    threading.Thread.__init__(self)

  def log_output(self, output):
    if (output is None):
      return
    data = output.decode("UTF-8")
    data = data.replace('\r\n', '\n').replace('\r', '\n')
    print(data)

  def run(self):
    worker = subprocess.Popen(args=self.cmd,
                              env=self.env,
                              startupinfo=self.startup_info,
                              stdout=(None if self.silent else subprocess.PIPE),
                              stderr=(None if self.silent else subprocess.PIPE))
    output, error = worker.communicate()
    self.log_output(output)


class CucumberFrontendThread(GenericRunnerThread):
  def __init__(self, cucumber, feature_dir):
    GenericRunnerThread.__init__(self, [ cucumber, feature_dir ], {})


class CukeWiredRunnerThread(GenericRunnerThread):
  def __init__(self, runner, runner_env):
    GenericRunnerThread.__init__(self, [ runner ], runner_env, silent=True)


class CukeTestwalkerCommand(sublime_plugin.WindowCommand):
  def automagically_locate(self, dir_name):
    try:
      viewed_file = self.window.active_view().file_name()
      return find_parent_dir(viewed_file, dir_name)
    except Exception as error:
      return None

  def run(self, **args):
    self.feature_dir = args.get('feature_dir', self.automagically_locate("features"))
    self.cucumber = args.get('cucumber', 'cucumber')
    self.runner = args.get('runner', None)
    self.runner_env = args.get('runner_env', None)

    if (self.feature_dir is None):
      raise ValueError('Argument `feature_dir` needs to be the path to a Gherkin `features` directory!')
    if (self.runner is None):
      raise ValueError('Argument `runner` needs to be the path to a runner executable!')

    runner_thread = CukeWiredRunnerThread(self.runner, self.runner_env)
    frontend_thread = CucumberFrontendThread(self.cucumber, self.feature_dir)
    runner_thread.start()
    frontend_thread.start()