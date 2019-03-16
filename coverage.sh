#!/bin/sh

set -e

COVERAGE_PROCESS_START=.coveragerc coverage run setup.py test
coverage combine
coverage html
coverage report
