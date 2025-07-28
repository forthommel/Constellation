"""
SPDX-FileCopyrightText: 2025 L. Forthomme, DESY and the Constellation authors
SPDX-License-Identifier: EUPL-1.2

Provides the satellite implementation for the Sampic TCP control interface
"""

import datetime
import socket
from typing import Any

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
    _extract_stream: bool = False
    _num_triggers_acquired: int = 0
    _run_name: str = ""
    _base_filename: str = ""

    def do_initializing(self, configuration: Configuration) -> str:
        self.log.info("Received configuration with parameters: %s", ", ".join(configuration.get_keys()))

        ip_address = configuration["ip_address"]
        port = configuration["port"]
        timeout = configuration.setdefault("timeout", 5.0)
        self._extract_stream = configuration.setdefault("extract_stream", False)
        self._run_name = configuration.setdefault("run_name", "run")
        self._base_filename = configuration.setdefault("base_filename", "sampic_run")

        try:
            self._sampic = SampicTCPController(str(ip_address), port=int(port), timeout=float(timeout))
            self._sampic.dataTransmitToTCPClient(self._extract_stream)
        except ConnectionRefusedError as e:
            raise RuntimeError(f"Connection refused to {ip_address}:{port} -> {str(e)}")

        self.BOR["fw_version"] = self._sampic.fwVersion()
        self.BOR["sw_version"] = self._sampic.swVersion()

        return f"Connected to Sampic at {ip_address}"

    def do_reconfigure(self, configuration: Configuration) -> str:
        if not self._sampic:
            return "Failed to reconfigure. Sampic is not connected."
        self._sampic.stop()
        return "Successfully reconfigured Sampic"

    def do_run(self, payload: Any) -> str:
        self._num_triggers_acquired = 0
        event_payload = bytearray()
        self._sampic.start(self._run_name, baseFilename=self._base_filename)
        first_event_sent = False
        while not self._state_thread_evt.is_set():
            if self._extract_stream:
                try:
                    self._sampic.read(event_payload, 1024)
                    self.data_queue.put(event_payload)
                    event_payload.clear()
                except socket.timeout:
                    self.log.warning("Timeout encountered while retrieving the frame.")
                    continue
                self._num_triggers_acquired += 1
                self.log.info(f"Fetched event {self._num_triggers_acquired}")
            elif not first_event_sent:
                first_event_sent = False

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
