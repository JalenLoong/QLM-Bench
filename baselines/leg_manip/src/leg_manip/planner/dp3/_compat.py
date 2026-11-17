"""Tiny shim so the vendored DP3 code does not need termcolor."""


def cprint(text, *args, **kwargs) -> None:
    del args, kwargs
    print(text)
