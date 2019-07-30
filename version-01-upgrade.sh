#!/bin/bash

VERSION_DIR="gencove/version"

MAJOR_FILE="$VERSION_DIR/A-major"
MINOR_FILE="$VERSION_DIR/B-minor"
PATCH_FILE="$VERSION_DIR/C-patch"


MAJOR=$(cat $MAJOR_FILE)
MINOR=$(cat $MINOR_FILE)
PATCH=$(cat $PATCH_FILE)

CURRENT="$MAJOR.$MINOR.$PATCH"

case $1 in
  major)
    echo "Updating major version number"
    OLD="$CURRENT"
    MAJOR=$(($MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    echo "Updating minor version number"
    OLD="$CURRENT"
    MINOR=$(($MINOR + 1))
    PATCH=0
    ;;
  patch)
    echo "Updating patch version number"
    OLD="$CURRENT"
    PATCH=$(($PATCH + 1))
    ;;
  print)
    echo "Current version number:"
    echo "$CURRENT"
    exit
    ;;
  *)
    echo "First argument must be one of the following:"
    echo "major"
    echo "minor"
    echo "patch"
    echo "print"
    exit 1
    ;;
esac

CURRENT="$MAJOR.$MINOR.$PATCH"

echo "New version number:"
echo $CURRENT

# Save only towards the end, when we're sure everything went OK
echo "Saving new version"
echo $MAJOR > $MAJOR_FILE
echo $MINOR > $MINOR_FILE
echo $PATCH > $PATCH_FILE

echo "Git add changes to $VERSION_DIR/:"
git add $VERSION_DIR

echo "Git commit changes"
git commit -m "Update app version to $CURRENT"

# # Tag only on binary changes for future rebuilds
# if [ "$1" = "major" ] || [ "$1" = "minor" ] || [ "$1" = "patch" ]; then
#   git tag -a "v$CURRENT" -m "App version tag: $CURRENT"
# fi