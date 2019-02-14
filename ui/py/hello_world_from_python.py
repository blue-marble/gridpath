from argparse import ArgumentParser
import os.path
import sys


def parse_arguments(arguments):
    """
    :return:
    """
    parser = ArgumentParser(add_help=True)

    # Scenario name and location options
    parser.add_argument("--write_dir",
                        help="Directory to write to.")

    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


def write_file(args=None):
    """

    :param args:
    :return:
    """
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args)
    write_path = parsed_args.write_dir

    print write_path

    with open(
            os.path.join(write_path, "hello_world_from_python.txt"), "w"
    ) as f:
        f.write("Hello World from Python!")


if __name__ == "__main__":
    write_file()
