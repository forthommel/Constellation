"""
SPDX-FileCopyrightText: 2025 L. Forthomme, DESY and the Constellation authors
SPDX-License-Identifier: EUPL-1.2

Provides the satellite implementation for the Sampic TCP control interface
"""

import datetime
import socket
import time
from typing import Any

from constellation.core.commandmanager import cscp_requestable
from constellation.core.configuration import Configuration
from constellation.core.message.cscp1 import CSCP1Message
from constellation.core.monitoring import schedule_metric
from constellation.core.protocol.cscp1 import SatelliteState
from constellation.core.satellite import Satellite
from SampicTCPController import SampicTCPController


class SampicTCPSatellite(Satellite):
    _sampic = None
    _sequence_mode: bool = False
    _num_triggers_acquired: int = 0
    _max_triggers: int = 0
    _run_name: str = ""
    _base_filename: str = ""

    def do_initializing(self, configuration: Configuration) -> str:
        self.log.info("Received configuration with parameters:\n%s", ",\n".join(configuration.get_keys()))

        ip_address: str = configuration.get_str("ip_address")
        port: int = configuration.get_int("port")
        timeout: float = configuration.get_float("timeout", 5.0e9)
        self._run_name = configuration.get_str("run_name", "run")
        self._base_filename = configuration.get_str("base_filename", "sampic_run")
        self._max_triggers = configuration.get_int("max_triggers", 0)

        try:
            self._sampic = SampicTCPController(ip_address, port=port, timeout=timeout)
            self._sampic.dataTransmitToTCPClient(False)
        except ConnectionRefusedError as e:
            raise RuntimeError(f"Connection refused to {ip_address}:{port} -> {str(e)}")

        return f"Connected to Sampic at {ip_address}"

    def do_reconfigure(self, configuration: Configuration) -> str:
        if not self._sampic:
            return "Failed to reconfigure. Sampic is not connected."
        self._sampic.stop()
        return "Successfully reconfigured Sampic"

    def do_run(self) -> str:
        self._num_triggers_acquired = 0
        max_triggers: int = self._max_triggers if self._max_triggers > 0 else -1
        self._sampic.start(self._base_filename, numTriggers=max_triggers, baseFilename=f"{self._run_name}")
        while not self.stop_requested():
            if self._sampic.finished():
                self._num_triggers_acquired = max_triggers
                return "Finished acquisition"
            time.sleep(0.1)
        self._sampic.stop()
        return "Finished acquisition"

    def do_stopping(self) -> str:
        self.log.info(f"Stopping the run after {self._num_triggers_acquired} event(s)")
        return "Stopped acquisition"

    @cscp_requestable([SatelliteState.RUN])
    def get_num_triggers(self, request: CSCP1Message) -> tuple[str, Any, dict[str, Any]]:
        return f"Number of triggers: {self._num_triggers_acquired}", self._num_triggers_acquired, {}

    @schedule_metric("", 10, allowed_states=[SatelliteState.RUN])
    def NUM_TRIGGERS(self) -> int | None:
        return self._num_triggers_acquired
