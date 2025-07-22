---
# SPDX-FileCopyrightText: 2025 Laurent Forthomme, DESY and the Constellation authors
# SPDX-License-Identifier: CC-BY-4.0 OR EUPL-1.2
title: "Sampic"
description: "Satellite controlling a Sampic ASIC digitiser using TCP commands"
---

## Description

This satellite uses the [SampicTCPController](https://pypi.org/project/SampicTCPController) library by L. Forthomme, to control via the TCP/IP protocol
the readout and extraction of all measurements from a Sampic ASIC module.
Given the Sampic control software is running on the computer the module is connected to, and has control through TCP commands switched on, this
wrapper will send and request frames until the end of a run, and handle the secured communication through the aforementioned library.
All frames are then transmitted through the [CDTP](https://constellation.pages.desy.de/protocols/cdtp.html) to Constellation receivers.

## Requirements

This satellite requires the `[sampic]` component, which can be installed with:

::::{tab-set}
:::{tab-item} PyPI
:sync: pypi

```sh
pip install ConstellationDAQ[sampic]
```

:::
:::{tab-item} Source
:sync: source

```sh
pip install --no-build-isolation -e .[sampic]
```

:::
::::


## Supported devices

This satellite is compatible with the Sampic ASIC encompassing ADCs for the digitisation of full waveforms with high channel multiplicities
(16 channels per mezzanine, and up to 2 mezzanines per module).
The device to be controlled by this satellite can be accessed via the `ip_address` and `port` configuration parameters.
The port number is linked to the master mezzanine serial number, and is therefore expected to be changed for each user with no default value.

## Parameters

| Parameter | Description | Type | Default Value |
|-----------|-------------|------|---------------|
| `ip_address` | Scope IP address | String | - |
| `port` | TCP port to connect to | Integer | 1861 |
| `timeout` | Timeout before giving up on frames retrieval | Float | 5s |

## Metrics

| Metric | Description | Value Type | Metric Type | Interval |
|--------|-------------|------------|-------------|----------|
| `NUM_TRIGGERS` | Number of triggers collected so far | Integer | `LAST_VALUE` | 10s |

## Custom Commands

| Command | Description | Arguments | Return Value | Allowed States |
|---------|-------------|-----------|--------------|----------------|
| `get_num_triggers` | Retrieve the number of triggers collected so far | - | Integer | any |

## Output data format

Data are packed as follows, using double precision floats for each word:

| Group | Word | Description |
|-------|------|-------------|
| Global header | Trigger times | Absolute timing of each trigger in the sequence |
|| Number of samples | Number of samples in all triggers in all sequences (run-level) |
| Channel header | Trigger offsets | Channel-level timing offset (with respect to the absolute timing in the global header) of each individual trigger in the sequence |
|| Wave array | Number of samples * number of triggers/sequence double precision floats providing the sample amplitude (in V) for the given time slice |

Additionally, a beginning-of-run event is generated with the following attributes:

| Parameter | Description | Type |
|-----------|-------------|------|
| `sampling_period` | Sampling period (in s) | Float |
