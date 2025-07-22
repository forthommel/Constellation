"""
SPDX-FileCopyrightText: 2025 L. Forthomme, DESY and the Constellation authors
SPDX-License-Identifier: EUPL-1.2

Provides the satellite implementation for the Sampic TCP control interface
"""

import datetime
import socket
from typing import Any

import numpy as np
from constellation.core.cmdp import MetricsType
from constellation.core.commandmanager import cscp_requestable
from constellation.core.configuration import Configuration
from constellation.core.datasender import DataSender
from constellation.core.message.cscp1 import CSCP1Message, SatelliteState
from constellation.core.monitoring import schedule_metric
from SampicTCPController import SampicTCPController


class SampicTCPSatellite(DataSender):
    _sampic = None
    _sequence_mode: bool = False
    _num_triggers_acquired: int = 0

    def do_initializing(self, configuration: Configuration) -> str:
        self.log.info("Received configuration with parameters: %s", ", ".join(configuration.get_keys()))

        ip_address = configuration["ip_address"]
        sampling_period = configuration["sampling_period"]
        port = configuration.setdefault("port", 1861)
        timeout = configuration.setdefault("timeout", 5.0)

        try:
            self._sampic = SampicTCPController.SampicTCPController(str(ip_address), port=int(port), timeout=float(timeout))
            self._sampic.dataTransmitToTCPClient(True)
        except ConnectionRefusedError as e:
            raise RuntimeError(f"Connection refused to {ip_address}:{port} -> {str(e)}")

        self.BOR["fw_version"] = self._sampic.fwVersion()
        self.BOR["sw_version"] = self._sampic.swVersion()
        self.BOR["sampling_period"] = float(sampling_period)

        return f"Connected to Sampic at {ip_address}"

    def do_reconfigure(self, configuration: Configuration) -> str:
        if not self._sampic:
            return "Failed to reconfigure. Sampic is not connected."
        self._sampic.stop()
        return "Successfully reconfigured Sampic"

    def do_run(self, payload: Any) -> str:
        self._num_triggers_acquired = 0
        event_payload = np.zeros(1024, np.int8())
        self._sampic.start()
        while not self._state_thread_evt.is_set():
            try:
                self._sampic.read(event_payload, 1024)
                self.data_queue.put((event_payload.tobytes(), {"dtype": f"{event_payload.dtype}"}))
            except socket.timeout:
                self.log.warning("Timeout encountered while retrieving the frame.")
                continue
            self._num_triggers_acquired += 1
            self.log.info(f"Fetched event {self._num_triggers_acquired}")

        self.EOR["current_time"] = datetime.datetime.now().timestamp()
        return "Finished acquisition"

    def do_stopping(self) -> str:
        self._sampic.stop()
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
