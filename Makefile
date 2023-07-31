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

all: bramz_pre_commit_hooks.egg-info/PKG-INFO

bramz_pre_commit_hooks.egg-info/PKG-INFO: env/.dev-requirements.stamp setup.py setup.cfg
	$(ENV_PYTHON) -m pip install --editable . --constraint dev-constraints.txt
	$(TOUCH) bramz_pre_commit_hooks.egg-info/PKG-INFO

env/.dev-requirements.stamp: env dev-requirements.txt dev-constraints.txt
	$(ENV_PYTHON) -m pip install --upgrade pip setuptools wheel --constraint dev-constraints.txt
	$(ENV_PYTHON) -m pip install --requirement dev-requirements.txt --constraint dev-constraints.txt
	$(TOUCH) env/.dev-requirements.stamp

env:
	$(PYTHON) -m venv env

clean:
	$(RMRF) bramz_pre_commit_hooks.egg-info
	$(RMRF) build

distclean: clean
	$(RMRF) env
	$(RMRF) .mypy_cache

.PHONY: all clean distclean
