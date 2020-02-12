# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Topic :: Software Development",
]

setup(
    name="immerframe",
    version="0.1.0",
    description="creates the next immutable object by simply "
    "modifying the current one",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=classifiers,
    keywords=[],
    author="Oliver Russell",
    author_email="ojhrussell@gmail.com",
    url="https://github.com/leontrolski/immerframe",
    license="MIT License",
    packages=find_packages(),
    extras_require=dict(testing=["pytest",],),
    install_requires=["attrs",],
    test_suite="pytest",
)
