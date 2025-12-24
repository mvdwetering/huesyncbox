#!/bin/bash
# bump_min_ha_version.sh
# Usage: ./bump_min_ha_version.sh <ha_version> <pytest_homeassistant_version>
# Example: ./bump_min_ha_version.sh 2025.3.0 0.13.215


set -e

# Determine the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -ne 2 ]; then
  echo "Usage: $0 <ha_version> <pytest_homeassistant_version>"

  # Get the previous version from hacs.json
  CURRENT_HA_VERSION=$(grep -oP '"homeassistant":\s*"\K[0-9.]+' "$SCRIPT_DIR/hacs.json" | head -n1)
  echo "Current minimum Home Assistant version is: $CURRENT_HA_VERSION"
  
  # Get current pytest-homeassistant-custom-component version
  CURRENT_PYTEST_HA_VERSION=$(grep -oP 'pytest-homeassistant-custom-component==\K[0-9.]+' "$SCRIPT_DIR/pyproject.toml" | head -n1)
  echo "Current pytest-homeassistant-custom-component version is: $CURRENT_PYTEST_HA_VERSION"
  exit 1
fi

NEW_VERSION="$1"
PYTEST_HA_VERSION="$2"

# Update homeassistant version in hacs.json
sed -i "s/\"homeassistant\": \"[0-9.]*\"/\"homeassistant\": \"$NEW_VERSION\"/" "$SCRIPT_DIR/hacs.json"

# Update homeassistant-stubs in pyproject.toml
sed -i "s/homeassistant-stubs==[0-9.]*/homeassistant-stubs==$NEW_VERSION/" "$SCRIPT_DIR/pyproject.toml"

# Update pytest-homeassistant-custom-component
sed -i "s/pytest-homeassistant-custom-component==[0-9.]*/pytest-homeassistant-custom-component==$PYTEST_HA_VERSION/" "$SCRIPT_DIR/pyproject.toml"

# Update minimum HA version in README.md
sed -i "s/Minimum required Home Assistant version is: [0-9.]*/Minimum required Home Assistant version is: $NEW_VERSION/" "$SCRIPT_DIR/README.md"

echo "Minimum HA version bumped to $NEW_VERSION in hacs.json, pyproject.toml, and README.md files."
echo "pytest-homeassistant-custom-component updated to $PYTEST_HA_VERSION."
