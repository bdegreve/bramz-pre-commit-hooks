import argparse
import datetime
import os
import re
from collections.abc import Sequence
from pathlib import Path

DEFAULT_PREFIX = "Copyright (C)"

SINGLE_YEAR_REGEX = re.compile(br"^\d{4}$")
YEAR_RANGE_REGEX = re.compile(br"^(?P<begin>\d{4})-(?P<end>\d{4})$")
CURRENT_YEAR = datetime.date.today().year


class Error(Exception):
    pass


def fix_copyright(
    filename: Path,
    *,
    dry: bool = False,
    prefix: str | None = None,
) -> None:
    prefix = prefix or DEFAULT_PREFIX
    pattern = rf"(?P<prefix>{re.escape(prefix)}\s*)(?P<years>\S+)"
    regex = re.compile(pattern.encode("utf-8"))

    content = filename.read_bytes()
    new_content, num = regex.subn(update_years, content)
    if num == 0:
        raise Error("No copyright line in file. Fix manually.")
    if new_content != content:
        if not dry:
            filename.write_bytes(new_content)
        raise Error("Copyright updated.")


def update_years(match: re.Match) -> bytes:
    original_line = match.group(0)
    prefix, years = match["prefix"], match["years"]

    try:
        current_year = int(os.environ["CURRENT_YEAR"])
    except KeyError:
        current_year = datetime.date.today().year

    if SINGLE_YEAR_REGEX.match(years):
        year = int(years)
        if year > current_year:
            raise Error(f"{year} is in the future. Fix manually.")
        if year == current_year:
            return original_line
        return prefix + f"{year}-{current_year}".encode("utf-8")

    if m := YEAR_RANGE_REGEX.match(years):
        begin, end = int(m["begin"]), int(m["end"])
        if begin > current_year or end > current_year:
            raise Error(f"{years} is in the future. Fix manually.")
        if end == current_year:
            return original_line
        return prefix + f"{begin}-{current_year}".encode("utf-8")

    raise Error(f"Unabled to parse copyright: {original_line}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", type=Path, nargs="*", help="Filenames to check")
    parser.add_argument("--dry", action="store_true", default=False)
    parser.add_argument("--prefix", help=f"default: {DEFAULT_PREFIX}")
    args = parser.parse_args(argv)

    ret = 0
    for filename in args.filenames:
        try:
            fix_copyright(filename, dry=args.dry, prefix=args.prefix)
        except Error as err:
            print(f"{filename}: {err}")
            ret = 1

    return ret
