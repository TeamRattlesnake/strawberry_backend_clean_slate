#!/usr/bin/bash

python -m pylint server/src/*.py --extension-pkg-whitelist='pydantic' --disable=too-many-instance-attributes,broad-exception-raised,line-too-long,unnecessary-pass,too-many-arguments,logging-fstring-interpolation,broad-exception-caught,invalid-name,too-many-return-statements,too-many-branches

python -m flake8 server/src/*.py --ignore E501,W503
