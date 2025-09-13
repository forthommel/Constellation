"""
SPDX-FileCopyrightText: 2025 L. Forthomme, DESY and the Constellation authors
SPDX-License-Identifier: EUPL-1.2

Provides the satellite implementation for the Sampic TCP control interface
"""

import datetime
import socket
import time
from typing import Any

from constellation.core.cmdp import MetricsType
from constellation.core.commandmanager import cscp_requestable
from constellation.core.configuration import Configuration
from constellation.core.message.cscp1 import CSCP1Message, SatelliteState
from constellation.core.monitoring import schedule_metric
from constellation.core.satellite import Satellite
from SampicTCPController import SampicTCPController


class SampicTCPSatellite(Satellite):
    _sampic = None
    _sequence_mode: bool = False
    _num_triggers_acquired: int = 0
    _run_name: str = ""
    _base_filename: str = ""

    def do_initializing(self, configuration: Configuration) -> str:
        self.log.info("Received configuration with parameters: %s", ", ".join(configuration.get_keys()))

        ip_address = configuration["ip_address"]
        port = configuration["port"]
        timeout = configuration.setdefault("timeout", 5.0)
        self._run_name = configuration.setdefault("run_name", "run")
        self._base_filename = configuration.setdefault("base_filename", "sampic_run")

        try:
            self._sampic = SampicTCPController(str(ip_address), port=int(port), timeout=float(timeout))
            self._sampic.dataTransmitToTCPClient(False)
        except ConnectionRefusedError as e:
            raise RuntimeError(f"Connection refused to {ip_address}:{port} -> {str(e)}")

        return f"Connected to Sampic at {ip_address}"

    def do_reconfigure(self, configuration: Configuration) -> str:
        if not self._sampic:
            return "Failed to reconfigure. Sampic is not connected."
        self._sampic.stop()
        return "Successfully reconfigured Sampic"

    def do_run(self, run_identifier: str) -> str:
        self._num_triggers_acquired = 0
        event_payload = bytearray()
        self._sampic.start(self._run_name, baseFilename=f"{self._base_filename}_{run_identifier}")
        first_event_sent = False
        while not self._state_thread_evt.is_set():
            time.sleep(0.1)

        self._sampic.stop()
        return "Finished acquisition"

    def do_stopping(self) -> str:
        self.log.info(f"Stopping the run after {self._num_triggers_acquired} event(s)")
        return "Stopped acquisition"

    @cscp_requestable
    def get_num_triggers(self, request: CSCP1Message) -> [str, int, dict[str, Any]]:
        if self.fsm.current_state_value == SatelliteState.RUN:
            return f"Number of triggers: {self._num_triggers_acquired}", self._num_triggers_acquired, {}
        return "Not running", -1, {}

    @schedule_metric("", MetricsType.LAST_VALUE, 10)
    def NUM_TRIGGERS(self) -> int | None:
        if self.fsm.current_state_value == SatelliteState.RUN:
            return self._num_triggers_acquired
        return None
