<p align="center">
	<img src="https://user-images.githubusercontent.com/9287847/50569701-4cf0f680-0d6c-11e9-93d9-f7c57983fc17.png"/ width="450" alt="exalt">
</p>

---

[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://python.org)
[![Not production ready](https://img.shields.io/badge/production%20ready-not%20really-red.svg)]()
[![Travis status](https://travis-ci.org/PhilipTrauner/exalt.svg?branch=master)](https://travis-ci.org/PhilipTrauner/exalt)

**exalt** provides a convenient way to dynamically create closures and bind them to a custom namespace. This is primarily useful for preserving an execution-context when calling into a different function.

## Example

```python
from exalt import promote


def baz():
    return bar


def foo():
    bar = "baz"

    return promote(baz, **locals())()


print(foo())
```
<p align="center"><b>↓</b></p>

```
baz
```

## Installation
```bash
pip3 install --user exalt
```

## Disclaimer
**exalt** heavily relies on CPython implementation details and probably shouldn't be used in a production environment.
