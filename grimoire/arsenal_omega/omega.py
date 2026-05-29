import argparse
from .modules.ghost_hollow import GhostHollow
from .modules.silicon_death import SiliconDeath
from .modules.data_harvester import DataHarvester

def _add_technique_subparsers(subparsers):
    GhostHollow.register(subparsers)
    SiliconDeath.register(subparsers)
    DataHarvester.register(subparsers)

def get_omega_parser():
    parser = argparse.ArgumentParser(prog="grimoire omega", add_help=True)
    sub = parser.add_subparsers(dest='technique', required=True)
    _add_technique_subparsers(sub)
    return parser

def register_omega_commands(subparsers):
    omega_parser = subparsers.add_parser('omega', help='Arsenal Omega')
    omega_sub = omega_parser.add_subparsers(dest='omega_technique', required=True)
    _add_technique_subparsers(omega_sub)
