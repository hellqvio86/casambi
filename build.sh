#/bin/bash
echo "Clean dirs"
rm -rf src/casambi.egg-info
rm -rf dist/*

echo "Build"
python3 setup.py sdist bdist_wheel

echo "Upload"
twine upload dist/*