[![Build Status](https://travis-ci.com/tomguyatt/datacaster.svg?branch=master)](https://travis-ci.com/tomguyatt/datacaster.svg?branch=master) [![codecov](https://codecov.io/gh/tomguyatt/datacaster/branch/master/graph/badge.svg)](https://codecov.io/gh/tomguyatt/datacaster) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)


# datacaster
Cast python dataclass arguments on instantiation


## Examples

A simple dataclass with `int`, `str`, `float`, and `Optional[int]` attributes.

The dataclass is decorated with `datacaster.decorators.cast_attributes`.

```python

from typing import Optional
from dataclasses import dataclass

from datacaster.decorators import cast_attributes

@cast_attributes
@dataclass
class TestClass:
    string: str
    integer: int
    floating: float
    optional_int: Optional[int] = None
```


When an instance of `TestClass` is created, the supplied arguments are type-checked and cast if necessary:

```python
In : TestClass(string=123, integer="123", floating=1)

Out: TestClass(string='123', integer=123, floating=1.0, optional_int=None)
```

```python
In : TestClass(string=None, integer=1.0, floating=1, optional_int="1")

Out: TestClass(string='None', integer=1, floating=1.0, optional_int=1)
```


Default values with invalid types will also be caught. This dataclass has a single keyword argument whose default value does not match the annotation:

```python
@cast_attributes
@dataclass
class TestClass:
    optional_int: Optional[int] = "hello"


print(TestClass())
```

When running the code above, the following exception is raised:

```console
InvalidDefaultValue: Default value 'hello' for field 'optional_int' should be type typing.Union[int, NoneType] but is a <class 'str'>. Please change the dataclass field type annotation or default value.
```
