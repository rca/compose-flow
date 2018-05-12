class NoSuchProfile(Exception):
    """
    Raised when a requested profile is not listed in dc.yml
    """


class TagVersionError(Exception):
    """
    Raised when there is a problem running tag-version
    """
