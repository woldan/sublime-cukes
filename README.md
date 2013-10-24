# Cucumber Helpers for the Sublime Text Editor

## Installation

Clone repository into your package directory (find out where it is vi `"Browse Packages..."`):

    cd <sublime 3 packages dir>
    git clone https://github.com/woldan/sublime-cukes.git Cukes

## Usage of the Cucumber Build System in a Project:

Add something like this to your @.sublime-project@ file:

    "build_systems":
    [
      {
        "name": "Cuke",
        "target": "cuke_testwalker",
      }
    ]

## Usage of a Wired Cucumber Build System

To use cucumber with the [wire protocol] https://github.com/cucumber/cucumber/wiki/Wire-Protocol)
use something like this in your @.sublime-project@ file:

    "build_systems":
    [
      {
        "name": "Cuke",
        "target": "cuke_testwalker",
        "runner": "/path/to/wired/runner",
        "runner_env": { "PATH": "/some/paths" }
      }
    ]

