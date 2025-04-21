from argparse import ArgumentParser

from dodo_commands import Dodo


def _args():
    # Create the parser
    parser = ArgumentParser(description="")

    # Use the parser to create the command arguments
    args = Dodo.parse_args(parser, config_args=[])
    args.cwd = Dodo.get("/ROOT/src_dir")

    return args


# Use safe=False if the script makes changes other than through Dodo.run
if Dodo.is_main(__name__, safe=True):
    args = _args()
    Dodo.run(["lcopy", ".lcopy/lcopy.lcopy_spec.yaml", "copy"], cwd=args.cwd)
    Dodo.run(["lcopy", ".lcopy/lcopy.lcopy_src.yaml", "copy"], cwd=args.cwd)
