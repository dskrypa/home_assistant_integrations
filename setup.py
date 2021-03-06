#!/usr/bin/env python

from itertools import chain
from pathlib import Path
from setuptools import setup

project_root = Path(__file__).resolve().parent
long_description = project_root.joinpath('readme.rst').read_text('utf-8')

about = {}
with project_root.joinpath('__version__.py').open('r', encoding='utf-8') as f:
    exec(f.read(), about)

# noinspection PyDictCreation
optional_dependencies = {
    'dev': [                                            # Development env requirements
        'ipython',
        'pre-commit',                                   # run `pre-commit install` to install hooks
    ],
}
optional_dependencies['ALL'] = sorted(set(chain.from_iterable(optional_dependencies.values())))
optional_dependencies['homeassistant'] = ['homeassistant']  # This should be installed with --no-deps

requirements = ['nest-client@ git+https://github.com/dskrypa/nest-client']


setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    description=about['__description__'],
    long_description=long_description,
    url=about['__url__'],
    project_urls={'Source': about['__url__']},
    packages=['nest_web'],
    package_dir={'': 'components'},
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='~=3.10',
    install_requires=requirements,
    extras_require=optional_dependencies,
)
