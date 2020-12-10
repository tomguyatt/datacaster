from setuptools import setup

TEST_DEPENDENCIES = [
    "pytest==4.6.3",
    "pytest-cov==2.8.1",
    "coverage==5.0",
    "typeguard==2.7.1",
]

setup(
    name="datacaster",
    description="Cast class attributes on instantiation.",
    version="0.10.0",
    author="Tom Guyatt",
    maintainer="Tom Guyatt",
    author_email="tomguyatt@gmail.com",
    maintainer_email="tomguyatt@gmail.com",
    url="https://github.com/tomguyatt/datacaster",
    packages=["datacaster"],
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=["typeguard==2.7.1"],
    tests_require=TEST_DEPENDENCIES,
    extras_require={"test": TEST_DEPENDENCIES},
    test_suite="tests",
)
