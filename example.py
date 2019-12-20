from typing import Optional
from dataclasses import dataclass

from datacaster import decorators


@decorators.cast_attributes
@dataclass(frozen=True)
class ExampleDataClass:
    string: str
    integer: int
    floating: float
    optional_string: Optional[str] = None


if __name__ == "__main__":
    print("All arguments supplied and valid...")
    print(ExampleDataClass(string="String", integer=123, floating=1.0, optional_string="I am optional!"))
    print("Casting simple mandatory and optional arguments...")
    print(ExampleDataClass(string=123, integer="123", floating=1, optional_string=123))
