#!/usr/bin/env python3
"""Helper script for release related tasks."""

import argparse
from enum import Enum
import logging
import subprocess
import json
import os
import re

from awesomeversion import AwesomeVersion  # type: ignore[import]

MASTER = "master"


class ReleaseType(Enum):
    MAJOR = 1
    MINOR = 2
    PATCH = 3


class ReleaseTypeModifier(Enum):
    NO = 1
    ALPHA = 2
    BETA = 3


class Branch:
    def __init__(self, name):
        self.name = name

    @property
    def is_dev(self):
        return self.name == "dev"

    @property
    def is_release(self):
        return self.name.startswith("release/")


class Git:

    @staticmethod
    def get_current_branch() -> Branch:
        branch_name = subprocess.check_output(["git", "branch", "--show-current"])
        return Branch(branch_name.decode("utf-8").strip())

    @staticmethod
    def workarea_is_clean() -> bool:
        return (
            subprocess.check_output(["git", "status", "--porcelain"])
            .decode("utf-8")
            .strip()
            == ""
        )

    @staticmethod
    def checkout(branch):
        subprocess.run(["git", "checkout", branch], check=True)

    @staticmethod
    def add_changes():
        subprocess.run(["git", "add", "--all"], check=True)

    @staticmethod
    def commit_changes(message):
        subprocess.run(["git", "commit", "-m", message], check=True)

    @staticmethod
    def pull():
        subprocess.run(["git", "pull"], check=True)

    @staticmethod
    def delete_branch(name):
        subprocess.run(["git", "branch", "-D", name], check=True)

    @staticmethod
    def create_branch(name):
        subprocess.run(["git", "branch", name], check=True)

    @staticmethod
    def create_tag(name):
        subprocess.run(["git", "tag", name], check=True)

    @staticmethod
    def push_to_origin(name):
        subprocess.run(["git", "push", "origin", name], check=True)

    @staticmethod
    def fetch_tags():
        subprocess.run(["git", "fetch", "--tags"], check=True)

def menu(title, choices):
    while True:
        print(title)
        for i, choice in enumerate(choices):
            print(f"  {i + 1} = {choice}")
        str_choice = input(": ")
        try:
            choice = int(str_choice)
        except ValueError:
            print("Invalid input, please enter a number")
            continue
        if choice in range(1, len(choices) + 1):
            return choices[choice - 1]
        else:
            print("Invalid input, please enter a valid number")


def enum_menu(title, enum_type):
    choices = [choice.name for choice in enum_type]
    return enum_type[menu(title, choices)]


def bump_version(
    version,
    major: bool = False,
    minor: bool = False,
    patch: bool = False,
    alpha: bool = False,
    beta: bool = False,
):
    major_number = version.major
    minor_number = version.minor
    patch_number = version.patch
    modifier = version.modifier or ""

    if major:
        major_number = int(major_number) + 1
        minor_number = 0
        patch_number = 0
        modifier = ""
    elif minor:
        minor_number = int(minor_number) + 1
        patch_number = 0
        modifier = ""
    elif patch:
        patch_number = int(patch_number) + 1
        modifier = ""

    if alpha:
        if not modifier:
            alpha_version = 0
        elif version.alpha:
            if match := re.search(r"\d+$", modifier):
                alpha_version = int(match.group()) + 1
        else:
            raise ValueError(
                "Bumping a non-alpha version (e.g. beta) to an alpha modifier is not supported"
            )
        modifier = f"a{alpha_version}"
    elif beta:
        if not modifier or version.alpha:
            beta_version = 0
        elif version.beta:
            if match := re.search(r"\d+$", modifier):
                beta_version = int(match.group()) + 1
        else:
            raise ValueError(
                "Bumping a non-beta version (e.g. rc) to a beta modifier is not supported"
            )
        modifier = f"b{beta_version}"

    return AwesomeVersion(f"{major_number}.{minor_number}.{patch_number}{modifier}")


def get_versions():
    version_tags = subprocess.check_output(["git", "tag", "-l", "v*"])

    awesome_versions = []
    for version_tag in version_tags.decode("utf-8").split("\n"):
        version = AwesomeVersion(version_tag[1:])
        if version.valid:
            awesome_versions.append(version)

    awesome_versions.sort()
    return awesome_versions


def get_integration_name():
    dir_list = [
        name
        for name in os.listdir("custom_components")
        if os.path.isdir(os.path.join("custom_components", name)) and name != "__pycache__"
    ]
    if len(dir_list) != 1:
        raise ValueError(
            f"Expected one directory below custom_components, but found {', '.join(dir_list)}"
        )
    return dir_list[0]


def update_manifest_version_number(version):
    manifest_file = "custom_components/{}/manifest.json".format(get_integration_name())

    with open(manifest_file) as f:
        manifest = json.load(f)

    manifest["version"] = str(version)
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)


def get_version_from_manifest():
    manifest_file = "custom_components/{}/manifest.json".format(get_integration_name())

    with open(manifest_file) as f:
        manifest = json.load(f)

    return AwesomeVersion(manifest["version"])


def get_last_released_version():
    versions = get_versions()
    logging.debug(f"All versions: {versions}")

    versions = [version for version in versions if not version.modifier]
    logging.debug(f"Real versions: {versions}")

    return versions[-1] if len(versions) > 0 else None


def main(args):
    branch = Git.get_current_branch()

    if not (branch.is_dev or branch.is_release):
        raise ValueError(
            f"Unexpected branch: {branch.name}, should be dev or release/x.y.z"
        )

    if not Git.workarea_is_clean():
        logging.error("Workarea is not clean")
        exit(1)

    Git.fetch_tags()

    manifest_version = get_version_from_manifest()
    print(f"Manifest version is {manifest_version}")

    # Alpha and beta modifiers are bumped after release when on a release branch
    bump_version_after_release = None

    if branch.is_dev:
        last_released_version = get_last_released_version()
        print(f"Last released version was {last_released_version}")

        if not last_released_version:
            print("First release, nice!")
            last_released_version = AwesomeVersion("0.0.0")

        release_type = enum_menu("What type of release is this?", ReleaseType)
        release_type_modifier = enum_menu(
            "Create releasebranch for alpha or beta?", ReleaseTypeModifier
        )

        next_version = bump_version(
            last_released_version,
            major=release_type == ReleaseType.MAJOR,
            minor=release_type == ReleaseType.MINOR,
            patch=release_type == ReleaseType.PATCH,
            alpha=release_type_modifier == ReleaseTypeModifier.ALPHA,
            beta=release_type_modifier == ReleaseTypeModifier.BETA,
        )

        # Release branch does not have alpha/beta modifiers
        release_branch_name = f"release/{AwesomeVersion(f'{next_version.major}.{next_version.minor}.{next_version.patch}')}"

    if branch.is_release:
        release_branch_name = branch.name

        # On release branch we can only bump alpha/beta, not major/minor/patch
        release_type_modifier = enum_menu(
            "Bump alpha or beta (no = release to master)?", ReleaseTypeModifier
        )

        if release_type_modifier == ReleaseTypeModifier.NO:
            next_version = AwesomeVersion(
                f"{manifest_version.major}.{manifest_version.minor}.{manifest_version.patch}"
            )
        else:
            next_manifest_version = bump_version(
                manifest_version,
                alpha=release_type_modifier == ReleaseTypeModifier.ALPHA,
                beta=release_type_modifier == ReleaseTypeModifier.BETA,
            )

            # Changing from alpha to beta should bump the version before release
            if manifest_version.alpha and next_manifest_version.beta:
                next_version = next_manifest_version
            else:
                next_version = manifest_version

    # Alpha and beta modifiers are (also) bumped after release
    if release_type_modifier != ReleaseTypeModifier.NO:
        bump_version_after_release = bump_version(
            next_version,
            alpha=release_type_modifier == ReleaseTypeModifier.ALPHA,
            beta=release_type_modifier == ReleaseTypeModifier.BETA,
        )

    tag_name = f"v{next_version}"
    logging.debug(f"Tag name: {tag_name}")

    print(f"On branch: {branch.name}")
    print(f"Release branch to use: {release_branch_name}")
    if bump_version_after_release:
        print(f"Bump version after release: {bump_version_after_release}")
    print(" ")

    if input(f"Confirm release of version {next_version}? [y/N]: ") != "y":
        exit(1)

    if branch.is_dev:
        Git.create_branch(release_branch_name)
        Git.checkout(release_branch_name)

    if branch.is_dev or (branch.is_release and not next_version.modifier):
        update_manifest_version_number(next_version)
        Git.add_changes()
        Git.commit_changes(f"Update version to {next_version}")

    if not next_version.modifier:
        # Merge to master
        Git.checkout(MASTER)
        Git.pull()
        subprocess.run(
            [
                "git",
                "merge",
                "--no-ff",
                release_branch_name,
                "--strategy-option",
                "theirs",
                "-m",
                f"Release v{next_version}",
            ]
        )

    Git.create_tag(tag_name)

    if bump_version_after_release:
        assert Git.get_current_branch() != MASTER
        update_manifest_version_number(bump_version_after_release)
        Git.add_changes()
        Git.commit_changes(f"Update version to {bump_version_after_release}")

    if input("Push to origin? [Y/n]: ") != "n":
        if Git.get_current_branch() == MASTER:
            Git.push_to_origin(MASTER)
        Git.push_to_origin(release_branch_name)
        Git.push_to_origin(tag_name)
    else:
        print("Don't forget to push later or revert changes!")

    print("Done!")
    print(f"Currently on branch: {Git.get_current_branch().name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Define loglevel, default is INFO.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    main(args)
