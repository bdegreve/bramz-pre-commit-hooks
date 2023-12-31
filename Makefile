ifdef ComSpec
	MKDIRP=powershell md -Force
	RMRF=powershell function rmrf ($$path) { if (Test-Path $$path) { Remove-Item -Recurse -Force $$path } }; rmrf
	TOUCH=powershell function touch ($$path) { if (Test-Path $$path) { (Get-ChildItem $$path).LastWriteTime = Get-Date } else { New-Item -ItemType file $$path } }; touch
	PYTHON=py
	ENV_PYTHON=env\Scripts\python.exe
else
	MKDIRP=mkdir -p
	RMRF=rm -rf
	TOUCH=touch
	PYTHON=python3
	ENV_PYTHON=env/bin/python
endif

all: bramz_pre_commit_hooks.egg-info/PKG-INFO format check

bramz_pre_commit_hooks.egg-info/PKG-INFO: env/.dev-requirements.stamp setup.py setup.cfg
	$(ENV_PYTHON) -m pip install --editable . --constraint dev-constraints.txt
	$(TOUCH) bramz_pre_commit_hooks.egg-info/PKG-INFO

env/.dev-requirements.stamp: env dev-requirements.txt dev-constraints.txt
	$(ENV_PYTHON) -m pip install --upgrade pip setuptools wheel --constraint dev-constraints.txt
	$(ENV_PYTHON) -m pip install --requirement dev-requirements.txt --constraint dev-constraints.txt
	$(ENV_PYTHON) -m pre_commit install
	$(TOUCH) env/.dev-requirements.stamp

env:
	$(PYTHON) -m venv env

format: env/.dev-requirements.stamp
	$(ENV_PYTHON) -m isort bramz_pre_commit_hooks
	$(ENV_PYTHON) -m black bramz_pre_commit_hooks

check: lint mypy

lint: env/.dev-requirements.stamp
	$(ENV_PYTHON) -m flake8 bramz_pre_commit_hooks

mypy: env/.dev-requirements.stamp
	$(ENV_PYTHON) -m mypy bramz_pre_commit_hooks

clean:
	$(RMRF) bramz_pre_commit_hooks.egg-info
	$(RMRF) build

distclean: clean
	$(RMRF) env
	$(RMRF) .mypy_cache

.PHONY: all format check lint mypy clean distclean
