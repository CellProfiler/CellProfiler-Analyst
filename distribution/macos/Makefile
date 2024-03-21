MAKEFLAGS += --warn-undefined-variables

SHELL := bash

.DEFAULT_GOAL := dist/CellProfiler-Analyst.app

.DELETE_ON_ERROR:

.SHELLFLAGS := -eu -o pipefail -c

.SUFFIXES:

CellProfiler-Analyst:
	git clone https://github.com/CellProfiler/CellProfiler-Analyst.git

	cd $@

.PHONY: dependencies
dependencies: CellProfiler-Analyst
	pip3 install --editable CellProfiler-Analyst --upgrade

dist/CellProfiler-Analyst.app: CellProfiler-Analyst dependencies Info.plist
	pyinstaller --noconfirm CellProfiler-Analyst.spec

	cp $(word 3, $^) $@/Contents

	cp entitlements.plist $@/Contents/MacOS

.PHONY: clean
clean:
	if [ -d CellProfiler-Analyst ]; then rm -rf CellProfiler-Analyst; fi

	if [ -d build ]; then rm -rf build; fi

	if [ -d dist ]; then rm -rf build; fi

	if [ CellProfiler.dmg ]; then rm -rf CellProfiler.dmg; fi
