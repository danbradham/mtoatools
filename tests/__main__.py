import os
import sys


def setup_path():
    mtoatools_path = os.path.join(os.path.dirname(__file__), '../')
    sys.path.insert(1, mtoatools_path)


def main():
    args = sys.argv[1:]

    if args and args[0] == '-matte_ui':
        setup_path()
        from tests import show_dialogs
        show_dialogs.matte_ui()
        return

    os.system('mayapy -m unittest discover tests -v')


if __name__ == '__main__':
    main()
