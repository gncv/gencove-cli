#!/bin/bash

VERSION_DIR="gencove/version"

MAJOR_FILE="$VERSION_DIR/A-major"
MINOR_FILE="$VERSION_DIR/B-minor"
PATCH_FILE="$VERSION_DIR/C-patch"

MAJOR=$(cat $MAJOR_FILE)
MINOR=$(cat $MINOR_FILE)
PATCH=$(cat $PATCH_FILE)

CURRENT="$MAJOR.$MINOR.$PATCH"

git tag -a "v$CURRENT" -m "App version tag: $CURRENT"
