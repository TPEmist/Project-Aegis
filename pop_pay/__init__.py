from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("pop-pay")
except PackageNotFoundError:
    __version__ = "unknown"
