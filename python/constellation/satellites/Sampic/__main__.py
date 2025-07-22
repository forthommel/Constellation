"""
SPDX-FileCopyrightText: 2024 DESY and the Constellation authors
SPDX-License-Identifier: EUPL-1.2

Provides the entry point for the Sampic TCP satellite
"""

from constellation.core.datasender import DataSenderArgumentParser
from constellation.core.logging import setup_cli_logging

from .SampicTCPSatellite import SampicTCPSatellite


def main(args=None) -> None:
    """Satellite controlling a Sampic ASIC digitiser through TCP commands"""

    # Get a dict of the parsed arguments
    parser = DataSenderArgumentParser(description=main.__doc__)
    args = vars(parser.parse_args(args))

    # Set up logging
    setup_cli_logging(args.pop("level"))

    # Start satellite with remaining args
    s = SampicTCPSatellite(**args)
    s.run_satellite()


if __name__ == "__main__":
    main()
