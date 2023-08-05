import os
import sys
import logging
import pathlib
import platform
from functools import wraps
from ctypes import c_char, CDLL
from typing import Optional, Callable, TypeVar, Any
from ctypes.util import find_library

T = TypeVar('T')

if platform.system() == 'Windows':
    from ctypes import windll as cdll  # type: ignore
else:
    from ctypes import cdll

logger = logging.getLogger(__name__)

# regexp for checking if an ipv4 address is valid.
ipv4 = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"


class ADict(dict):
    """
    Accessing dict keys like an attribute.
    """
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__  # type: ignore


class Snap7Library:
    """Snap7 loader and encapsulator. We make this a singleton to make
        sure the library is loaded only once.

    Attributes:
        lib_location: full path to the `snap7.dll` file. Optional.
    """
    _instance = None
    lib_location: Optional[str] = None

    def __new__(cls, lib_location: Optional[str] = None) -> "Snap7Library":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, lib_location: Optional[str] = None) -> None:
        """ Loads the snap7 library using ctypes cdll.

        Args:
            lib_location: full path to the `snap7.dll` file. Optional.

        Raises:
            RuntimeError: if `lib_location` is not found.
        """
        if hasattr(self, "cdll") and self.cdll is not None:
            return
        self.lib_location = (lib_location
                             or self.lib_location
                             or find_in_package()
                             or find_library('snap7')
                             or find_locally('snap7'))
        if not self.lib_location:
            raise RuntimeError("can't find snap7 library. If installed, try running ldconfig")
        self.cdll: CDLL = cdll.LoadLibrary(self.lib_location)


def load_library(lib_location: Optional[str] = None) -> CDLL:
    """Loads the `snap7.dll` library.
    Returns:
        cdll: a ctypes cdll object with the snap7 shared library loaded.
    """
    return Snap7Library(lib_location).cdll


def error_hadler_decorator(context: str = "client") -> Callable[..., Callable[..., int]]:
    """Decorator to handle error code returned by a decorated function.

    Args:
        context (str, optional): The context in which the decorated function is called.
            Default is "client". Possible values are "server", "client", or "partner".

    Returns:
        Callable: A decorator function that handles errors and checks the error code.
    """
    def decorator(func: Callable[..., int]) -> Callable[..., int]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> int:
            code = func(*args, **kwargs)
            check_error(code, context=context)
            return code
        return wrapper
    return decorator

def check_error(code: int, context: str = "client") -> None:
    """Check if the error code is set. If so, a Python log message is generated
        and an error is raised.

    Args:
        code: error code number.
        context: context in which is called.

    Raises:
        RuntimeError: if the code exists and is different from 1.
    """
    if code and code != 1:
        error = error_text(code, context)
        logger.error(error)
        raise RuntimeError(error)


def error_text(error: int, context: str = "client") -> bytes:
    """Returns a textual explanation of a given error number

    Args:
        error: an error integer
        context: context in which is called from, server, client or partner

    Returns:
        The error.

    Raises:
        TypeError: if the context is not in `["client", "server", "partner"]`
    """
    if context not in ("client", "server", "partner"):
        raise TypeError(f"Unkown context {context} used, should be either client, server or partner")
    logger.debug(f"error text for {hex(error)}")
    len_ = 1024
    text_type = c_char * len_
    text = text_type()
    library = load_library()
    if context == "client":
        library.Cli_ErrorText(error, text, len_)
    elif context == "server":
        library.Srv_ErrorText(error, text, len_)
    elif context == "partner":
        library.Par_ErrorText(error, text, len_)
    return text.value


def find_locally(fname: str = "snap7") -> Optional[str]:
    """Finds the `snap7.dll` file in the local project directory.

    Args:
        fname: file name to search for. Optional.

    Returns:
        Full path to the `snap7.dll` file.
    """
    file = pathlib.Path.cwd() / f"{fname}.dll"
    if file.exists():
        return str(file)
    return None


def find_in_package() -> Optional[str]:
    """Find the `snap7.dll` file according to the os used.

    Returns:
        Full path to the `snap7.dll` file.
    """
    basedir = pathlib.Path(__file__).parent.absolute()
    if sys.platform == "darwin":
        lib = 'libsnap7.dylib'
    elif sys.platform == "win32":
        lib = 'snap7.dll'
    else:
        lib = 'libsnap7.so'
    full_path = basedir.joinpath('lib', lib)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return str(full_path)
    return None
