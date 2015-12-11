import os
import sys


def main():
    args = sys.argv[1:]

    if not args or args[0] == '-ui':

        from tests import test_dialogs
        test_dialogs.test_matte_ui()


if __name__ == '__main__':
    main()
