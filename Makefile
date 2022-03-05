purge_cache:
	rm -r .coverage .mypy_cache/ .pytest_cache/
purge_full_cache:
	rm -r .coverage .mypy_cache/ .pytest_cache/ .tox/
build: setup.py
	rm -rf build/ dist/ src/mrkup.egg-info/
	python3 setup.py sdist bdist_wheel
update_upload: dist/
	python3 -m twine upload --skip-existing dist/* 
