from setuptools import setup

TEST_DEPENDENCIES = ["pytest==4.6.3"]

setup(
    name="datacaster",
    description="Cast dataclass attributes on object instantiation.",
    version="0.1.0",
    author="Tom Guyatt",
    maintainer="Tom Guyatt",
    author_email="tomguyatt@gmail.com",
    maintainer_email="tomguyatt@gmail.com",
    url="http://www.",
    packages=["src"],
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - production",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[],
    tests_require=TEST_DEPENDENCIES,
    extras_require={"test": TEST_DEPENDENCIES},
    test_suite="tests",
)
