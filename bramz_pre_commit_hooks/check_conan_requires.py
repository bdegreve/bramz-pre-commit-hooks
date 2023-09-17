# Copyright 2023 Bram de Greve
#
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of
#    conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list
#    of conditions and the following disclaimer in the documentation and/or other
#    materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be
#    used to endorse or promote products derived from this software without specific
#    prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

import argparse
import ast
import re
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple, TypeGuard

ALLOW_VERSION = (
    r"^\d+(\.\d+)*[a-zA-Z]?(-\d+)?(\+g[a-f0-9]+)?$"  # 1, 1.2.3.4, 1.2.3-4+g1234567
    + r"|^cci\.\d{8}$"  # cci.20210101
)
DENY_VERSION = r"local|dev|edit"

REQUIRES_ATTRIBUTES = (
    "requires",
    "tool_requires",
    "build_requires",
    "test_requires",
    "python_requires",
)

REQUIREMENTS_METHODS = (
    "requirements",
    "build_requirements",
)


class Patterns(NamedTuple):
    allow_version: re.Pattern
    deny_version: re.Pattern
    allow_user: re.Pattern
    allow_channel: re.Pattern


def check_conan_requires(filename: Path, *, patterns: Patterns):
    content = filename.read_text(encoding="utf-8")
    tree = ast.parse(content)
    has_conanfile = False
    for node in ast.walk(tree):
        if _is_conanfile(node):
            has_conanfile = True
            yield from _check_conanfile_class(node, patterns=patterns)
    if not has_conanfile:
        yield 0, 0, "ConanFile class not found"


def _is_conanfile(node: ast.AST) -> TypeGuard[ast.ClassDef]:
    return isinstance(node, ast.ClassDef) and any(
        base.id == "ConanFile" for base in node.bases if isinstance(base, ast.Name)
    )


def _check_conanfile_class(node: ast.ClassDef, *, patterns: Patterns):
    for stmt in node.body:
        if _is_requires_attribute(stmt):
            yield from _check_requires_attribute(stmt, patterns=patterns)
        elif _is_requirements_method(stmt):
            yield from _check_requirements_method(stmt, patterns=patterns)


def _is_requires_attribute(node: ast.AST) -> TypeGuard[ast.Assign]:
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in REQUIRES_ATTRIBUTES
    )


def _check_requires_attribute(node: ast.Assign, *, patterns: Patterns):
    if isinstance(node.value, (ast.List, ast.Tuple)):
        for value in node.value.elts:
            yield from _check_requirement(value, patterns=patterns)
    elif isinstance(node.value, ast.Constant):
        yield from _check_requirement(node.value, patterns=patterns)
    else:
        yield node.lineno, node.col_offset, "Conan requirement must be a list or tuple"


def _is_requirements_method(node: ast.AST) -> TypeGuard[ast.FunctionDef]:
    return isinstance(node, ast.FunctionDef) and node.name in REQUIREMENTS_METHODS


def _check_requirements_method(node: ast.FunctionDef, *, patterns: Patterns):
    for stmt in node.body:
        for nd in ast.walk(stmt):
            if isinstance(nd, ast.Call):
                if (
                    isinstance(nd.func, ast.Attribute)
                    and nd.func.attr in REQUIRES_ATTRIBUTES
                ):
                    yield from _check_requirement(
                        nd.args[0],
                        patterns=patterns,
                    )


def _check_requirement(node: ast.AST, *, patterns: Patterns):
    if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
        yield node.lineno, node.col_offset, "Conan requirement must be a string"
        return
    reference = node.value
    try:
        _name, version, user, channel = _split_reference(reference)
    except ValueError:
        yield (
            node.lineno,
            node.col_offset,
            f"Conan requirement {reference!r} is invalid",
        )
        return
    if patterns.deny_version.search(version):
        yield (
            node.lineno,
            node.col_offset,
            f"Conan requirement {reference!r} version is denied",
        )
        return
    if not patterns.allow_version.search(version):
        yield (
            node.lineno,
            node.col_offset,
            f"Conan requirement {reference!r} version is not allowed",
        )
        return
    if not patterns.allow_user.search(user):
        yield (
            node.lineno,
            node.col_offset,
            f"Conan requirement {reference!r} user is not allowed",
        )
        return
    if not patterns.allow_channel.search(channel):
        yield (
            node.lineno,
            node.col_offset,
            f"Conan requirement {reference!r} channel is not allowed",
        )
        return


def _split_reference(reference: str) -> tuple[str, str, str, str]:
    if "@" in reference:
        package, user_channel = reference.split("@")
        user, channel = user_channel.split("/")
    else:
        package = reference
        user, channel = "_", "_"
    name, version = package.split("/")
    return name, version, user, channel


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Conan requirements")
    parser.add_argument("filenames", type=Path, nargs="*", help="Filenames to check")
    parser.add_argument(
        "--allow-version",
        type=str,
        default=ALLOW_VERSION,
        help="Regular expression with allowed versions. default: %(default)s",
    )
    parser.add_argument(
        "--deny-version",
        type=str,
        default=DENY_VERSION,
        help="Regular expression with denied versions. default: %(default)s",
    )
    parser.add_argument(
        "--allow-user",
        type=str,
        default="^_$",
        help="Regular expression with allowed users. default: %(default)s",
    )
    parser.add_argument(
        "--allow-channel",
        type=str,
        default="^_$",
        help="Regular expression with allowed channels. default: %(default)s",
    )

    args = parser.parse_args(argv)

    patterns = Patterns(
        allow_version=re.compile(args.allow_version),
        deny_version=re.compile(args.deny_version),
        allow_user=re.compile(args.allow_user),
        allow_channel=re.compile(args.allow_channel),
    )

    ret = 0
    for filename in args.filenames:
        for lineno, col_offset, msg in check_conan_requires(
            filename, patterns=patterns
        ):
            print(f"{filename}:{lineno}:{col_offset}: {msg}")
            ret = 1

    return ret
