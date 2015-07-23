find . -name '*.py'| grep -v migrations | grep -v __init__.py | grep -v manage.py | grep -v formwizard | grep -v vendor | grep -v fabfile | grep -v static | grep -v nested_inlines | xargs pylint --load-plugins=pylint_django --rcfile=pylint.conf -r n 2>&1

#| grep -v recursion
