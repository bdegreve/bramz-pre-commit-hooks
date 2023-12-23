# bramz-pre-commit-hooks

Some [pre-commit](https://pre-commit.com/) hooks

## bramz-fix-copyright

Automatically update copyright years when source files are modified. Currently only
scans Python, C++ and C files.

It scans for strings like "Copyright 2022-2023 Bram de Greve" in your source code, and
will update the year range to include the current year. If no such string is found,
this hook will fail, telling you to manually add a copyright line, i.e. it doesn't
automatically add copyright information if none is there yet.

More specifically, the string it searches is `<PREFIX> <YEARS> <AUTHOR>` with `<PREFIX>`
being "Copyright" by default, and `<YEARS>` being either a single year like "2023", or
a single year range like "2022-2023".
```
- repo: https://github.com/bdegreve/bramz-pre-commit-hooks.git
  rev: babbefa12095ed4ee7270715044148bff66d2735
  hooks:
  - id: bramz-fix-copyright
    args: [--author=Bram de Greve]
```

### Options:

- `--author=<AUTHOR>`: REQUIRED. The string to be matched after the `<YEARS>` range.
- `--prefix=<PREFIX>`: The string to be mached before the `<YEARS>` range. By default,
  this is the string `Copyright`.
- `--license-file=<PATH>`: Additional file of which the copyright line must be updated,
  if any source file is changed. Is empty by default.

## bramz-check-conan-requires

Checks requirements in `conanfile.py` to verify if they match allowed patterns.

You can use this to prevent requirements to local references to be accidentily
committed.

```
- repo: https://github.com/bdegreve/bramz-pre-commit-hooks.git
  rev: babbefa12095ed4ee7270715044148bff66d2735
  hooks:
  - id: bramz-check-conan-requires
```

### Options

- `--allow-version=^\d+(\.\d+)*[a-zA-Z]?(-\d+)?(\+g[a-f0-9]+)?$|cci\.\d{8}$`. Regular
  expression of allowed versions. By default, this allows semver versions like `1`,
  `1.2`, `1.2.3`, `1.2.3.4`, `1.2.3-4`, `1.2.3-4+g1234567`, and CCI versions like
  `cci.20231201`.
- `--deny-version=local|dev|edit`. Regular expression of prohibited version strings
- `--allow-user=^_$`. Regular expression of allowed user strings. By default this only
  allows the "empty" user `_`.
- `--allow-channel=^_$`. Regular expression of allowed channel strings. By default this
  only allows the "empty" channel `_`.
