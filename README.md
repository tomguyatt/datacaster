[![Build Status](https://travis-ci.com/tomguyatt/datacaster.svg?branch=master)](https://travis-ci.com/tomguyatt/datacaster.svg?branch=master) [![codecov](https://codecov.io/gh/tomguyatt/datacaster/branch/master/graph/badge.svg)](https://codecov.io/gh/tomguyatt/datacaster) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)


# datacaster

Type-check & cast attributes on class instance creation. Uses the excellent `typeguard` project (https://github.com/agronholm/typeguard).

## Why

#### 1) Single point of config

Having written integrations for multiple third-party APIs and applications, I wanted an easy way to describe the following about each 'endpoint' object I was interested in:

- Record name
- Record fields
- Field types

#### 2) Ignoring superfluous data

Sometimes APIs give you way more information than you care about. I was keen to avoid writing comprehensions that iterate over a JSON response, and only pass fields to a constructor if the field name is in our field list.

#### 3) Incomplete data/inconsistent APIs

On the other hand - sometimes an API will not return a full object, depending on which operation you're performing (looking at you, Office365 Graph API). Again I wanted to avoid comprehensions that use `.get()` every time when passing fields to the constructor. It's a repeated pattern in the work I've been doing and basically boilerplate.

#### 4) Run time type-checking

Always useful.

#### 5) Custom casting for special attributes

I wanted a simple way to define functions that mutate/cast special attributes on instantiation. The `ObjectGUID` attribute in Active Directory, for example.

## What

Any class that inherits from `datacaster.classes.CastDataClass` **must**:

- Use the same annotations syntax you'd use in a dataclass.
- **Not** have an `__init__` defined.

During instance creation, the `CastDataClass.__init__` will:

1) Type-check the default values of any attributes that will **fall back to their default value**.
2) Unless the class annotation contains `IGNORE_EXTRA=False`, any extra attributes supplied to the constructor will be ignored.
3) Unless the class annotation contains `SET_MISSING_NONE=False`, any missing attributes will be set to None, regardless of their annotation.
4) Type-check all attributes passed to the constructor. If any attribute fails the type-check, the following will happen:

    - **If** an instance method exists for the attribute (`__cast__[attribute_name]__`), the value will be passed into that function, and the return value will be used in the class instance.
    
    - **Else** if the value is a value we can cast automatically, this will be attempted.

## Examples

A class that describes an Active Directory user. For simplicity a lot of 'useful' fields have been left out of the example.

```python
from typing import Optional, List

from datacaster.classes import CastDataClass


class User(CastDataClass):
    adminCount: Optional[int]
    badPwdCount: Optional[int]
    carLicense: List[str]
    cn: Optional[str]
    countryCode: Optional[str]
    displayName: Optional[str]
    distinguishedName: str
    givenName: Optional[str]
    info: Optional[str]
    lastLogoff: Optional[str]
    logonCount: Optional[int]
    mail: Optional[str]
    manager: Optional[str]
    memberOf: List[str]
    name: Optional[str]
    objectCategory: str
    objectClass: List[str]
    objectGUID: str
    objectSid: str
    primaryGroupID: int
    sAMAccountName: str
    sAMAccountType: Optional[int]
    sn: Optional[str]
    userAccountControl: int
    userPrincipalName: str
    
    def __cast_objectGUID__(self, value):
        # This will be called when the __init__ is inspecting the objectGUID
        # attribute. Here you can operate on the value passed to the constructor
        # and return whatever you need.
        return value
    
    def __cast_objectSid__(self, value):
        # As above, this will be called when the __init__ is inspecting the objectSid
        # attribute. Here you can operate on the value passed to the constructor and
        # return whatever you need.
        return value

```
