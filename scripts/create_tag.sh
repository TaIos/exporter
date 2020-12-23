#!/bin/bash

git tag -a "v$1" -m "Version $1"
git push --tags

