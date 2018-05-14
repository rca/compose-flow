class CommandError(Exception):
    """
    Raised when a problem with the command run is encountered
    """


class NoSuchProfile(Exception):
    """
    Raised when a requested profile is not listed in dc.yml
    """


class TagVersionError(Exception):
    """
    Raised when there is a problem running tag-version
    """
