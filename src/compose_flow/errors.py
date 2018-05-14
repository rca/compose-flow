class CommandError(Exception):
    """
    Raised when a problem with the command run is encountered
    """

class ErrorMessage(Exception):
    """
    Subclass to print out error message instead of entire stack trace
    """


class NoSuchProfile(Exception):
    """
    Raised when a requested profile is not listed in dc.yml
    """


class ProfileError(ErrorMessage):
    """
    Raised when there is a problem with a Profile
    """


class TagVersionError(Exception):
    """
    Raised when there is a problem running tag-version
    """
