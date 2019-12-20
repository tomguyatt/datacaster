from setuptools import setup

TEST_DEPENDENCIES = [
    "mock==2.0.0",
    "osirium-mockldap~=0.0",
    "osirium-test-devices==0.6.0",
    "pip_check_reqs==2.0.3",
    "pylint==2.3.1",
    "pytest==4.6.3",
    "pytest-cov==2.7.1",
    "pytest-mock==1.10.4",
]

setup(
    name="osirium-active-directory",
    version="3.4.5",  # https://semver.org/
    author="Osirium",
    maintainer="Osirium",
    author_email="supportdesk@osirium.com",
    maintainer_email="supportdesk@osirium.com",
    url="http://www.Osirium.com/PPA",
    packages=["active_directory"],
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - production",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=["python-ldap~=3.0", "osirium-ppa~=1.0"],
    tests_require=TEST_DEPENDENCIES,
    extras_require={"test": TEST_DEPENDENCIES},
    test_suite="tests",
)
