# python3-ev3dev-testfs

A FUSE file system for simulating ev3dev kernel devices.


## What can it do?

* Provide a Python API for creating "virtual" ev3dev devices, such as motors
  and sensors.
* Provide an executable Python script that can be used by other programming
  languages.


## Prerequisites

* **Linux**: This project is designed to only run on Linux. We will not support
  other operating systems.
* **Python 3**: This project requires a Python 3 runtime even when used by other
  programming languages.

For developers only:

* **Pipenv**: [Pipenv][pipenv] should be in your `PATH`.
* **Visual Studio Code**: This project prefers [Visual Studio Code][vscode] for
  development.


[pipenv]: https://pipenv.readthedocs.io/en/latest/


## Example Usage

TODO


## Hacking

### The VS Code Way


* In a terminal:

      git clone https://github.com/ev3dev/python-ev3dev-testfs
      cd python-ev3dev-testfs
      pipenv install
      code .

* Install the recommended extensions.

* Run the unit tests.

* Write a test that fails.

* Fix it.

* Commit it.

* Make a pull request.


### The Command Line Way

    git clone https://github.com/ev3dev/python-ev3dev-testfs
    cd python-ev3dev-testfs
    pipenv install
    pipenv shell
    python setup.py test  # run the unit tests
    python setup.py lint  # run the linter
    python setup.py doc  # build the docs
    python setup.py develop  # install the package in 'develop' mode
