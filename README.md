[![Build Status](https://travis-ci.com/tomguyatt/datacaster.svg?branch=master)](https://travis-ci.com/tomguyatt/datacaster.svg?branch=master) [![codecov](https://codecov.io/gh/tomguyatt/datacaster/branch/master/graph/badge.svg)](https://codecov.io/gh/tomguyatt/datacaster) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)


# datacaster

Runtime type-checking & attribute processing during class instance creation.

Uses the excellent `typeguard` project (https://github.com/agronholm/typeguard).

## Why

### Working with APIs

An integration between your own code & a third-party API is a data boundary.

They can be grey areas where you try to enforce some measure of sanity before the data enters your own code base.

I've experienced a few pain points while writing integrations for multiple third-party APIs & applications:

#### Data Types

Values in API responses can be the wrong type. You may also need to perform extra processing on certain values.

Active Directory is a good example. Some attributes need extra processing to be useful, like:
 
 - _objectSid_
 - _objectGUID_
 - _pwdLastSet_
 - _logonHours_

Datacaster allows you to define functions to pass values through before the new object is instantiated.

You can write functions for certain types _or_ specific fields.

#### Superfluous Values

More often than not you only care about a subset of the fields you get back from an API endpoint.

If the API doesn't support server-side filtering, you have to do it client-side.

Datacaster classes will ignore the fields you don't care about by default (this can be overridden).

#### Incomplete/Inconsistent API Data

Once you've defined what each endpoint object looks like, it doesn't mean you'll always receive every value from the API itself.

I've found Office365 Graph API will return inconsistent user fields depending on which API call you use.

If a field may/may not be missing from the response, you have to use `.get()` (or something to that effect) to handle missing values.

Datacaster sets missing fields to `None` by default (this can be overridden).

#### Run time type-checking

Supplied fields & values are type-checked at runtime thanks to `typeguard.check_type`.

The result of this check determines whether a field's value should be processed or not.

However, if you ___always___ want to process certain fields, this is also supported by datacaster.

Default field values are also type-checked.


## Using Datacaster

### Basic Example

This is a very basic example showing some features of datacaster.

#### Identifying the Need

A hypothetical API delivers data in 2 problematic ways:

- The `age` field is always sent as a string

- The `email_address` field is not mandatory & may not exist

- The `groups` field is:
 
    - A string if the user is in 1 group
    - A list if they are in 0 or > 1
    - Non-existent if they are not in any

#### Creating the class

- A simple `User` class is defined with 5 fields, inheriting from `datacaster.classes.CastDataClass`

- A new `user` object is created using the response from this hypothetical API

```python
from typing import Optional, List

from datacaster.classes import CastDataClass

class User(CastDataClass):
    first_name: str
    surname: str
    age: int
    email_address: Optional[str]
    groups: List[str]

user = User(**{"first_name": "duck", "surname": "adams", "age": "40", "groups": "sales"})
```

#### The Created Class Instance

- Datacaster casts the `age` to an `int` automatically

- The email address is missing so it is set to None

- The string `groups` field is cast to a list automatically

```python
User(first_name='duck', surname='adams', age=40, email_address=None, groups=['sales'])
```

#### Why not a Dataclass?

If you used a normal dataclass like this...

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    first_name: str
    surname: str
    age: int
    email_address: Optional[str]
    groups: List[str]
```

...you'd get:
 
 - a __TypeError__ if `email_address` or `groups` weren't supplied
 - both the `age` & `groups` fields would still be strings if supplied

You could make `email_address` default to `None`, but that can get frustrating.
 
When dealing with inconsistent APIs you'd have to know which fields may not exist.
