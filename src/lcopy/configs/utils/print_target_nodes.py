from pprint import pprint

from dataclassy import asdict


def print_target_nodes(target_nodes):
    for t in target_nodes:
        pprint(asdict(t), indent=2)
