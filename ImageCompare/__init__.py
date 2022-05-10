from .imagecompare import ImageCompare
from importlib import metadata

try:
    __version__ = metadata.version("robotframework-imagecompare")
except metadata.PackageNotFoundError:
    pass