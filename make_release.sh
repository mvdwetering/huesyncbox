#!/bin/bash

INFO='\033[0;36m'
ERROR='\033[0;31m'
NC='\033[0m' # No Color

# Check if version is given
if [ -z $1 ]; then
  echo -e "${ERROR}No version given. E.g '1.2.3'${NC}"
  exit 1
fi

version=$1
releasebranch=release/$version

pattern="^[0-9]+\.[0-9]+\.[0-9]+$"
if ! [[ $version =~ ${pattern} ]] ;
then
  echo -e "${ERROR}Version '$version' has incorrect format. Should be major.minor.patch e.g. '1.2.3'${NC}"
  exit 1
fi

# Check if clean
if [[ -n "$(git status --porcelain)" ]];
then
  echo -e "${ERROR}Working directory not clean${NC}"
  exit 1
fi

# Check if on dev
if branch=$(git symbolic-ref --short -q HEAD)
then
  if [[ $branch != "dev" ]]
  then
    echo -e "${ERROR}Not on 'dev' branch${NC}"
    exit 1
  fi
else
  echo -e "${ERROR}Not on a branch${NC}"
  exit 1
fi

# Check if version is "0.0.0" as it should be on dev
# Use loop to keep script repo independant
for manifest in custom_components/*/manifest.json
do
  result=$(jq '.version|contains("0.0.0")' $manifest)
  if [[ $result != 'true' ]]
  then
    echo -e "${ERROR}Manifest version is not 0.0.0.${NC}"
    exit 1
  fi
done

# Create release branch
git checkout -b $releasebranch

# Update manifest
# Use loop to keep script repo independant
echo -e "${INFO}Update version in manifest${NC}"
for manifest in custom_components/*/manifest.json
do
  new_manifest="$(jq '.version=$version' --arg version $version $manifest)"
  echo "${new_manifest}" > $manifest
done

git add --all
git commit -m "Update version to $version"

# Merge to master
echo -e "${INFO}Merge to master${NC}"
git checkout master
git pull
git merge --no-ff $releasebranch --strategy-option theirs -m "Release v$version"
git branch -D $releasebranch

echo -e "${INFO}Create tag${NC}"
git tag "v$version"


echo -e "${INFO}Done making release $version"
echo -e "Verify and push when happy (don't forget the tags)"
echo -e "${NC}"
echo -e "${ERROR}**************************************************"
echo -e "After that switch back to 'dev' !!!"
echo -e "**************************************************${NC}"
