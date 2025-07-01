import json

from dataclassy import asdict


def print_target_nodes(target_nodes):
    for t in target_nodes:
        print(json.dumps(asdict(t), indent=2))
