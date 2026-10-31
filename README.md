# V2V NR-V2X / PC5 Capstone Simulation Platform

This project is a research-oriented **simulation abstraction** of a 5G NR-V2X sidelink/PC5 V2V system. It is designed to be runnable on Windows with Python 3.11+ **without pygame**.

It is NOT a conformance implementation of 3GPP NR sidelink and it does not transmit real PC5 RF packets. The simulator models the important system-level behaviors so that the application/dissemination/security layers can later be connected to real hardware.

## Architecture

SUMO / manual mobility
        |
        v
Vehicle dynamics
        |
        +--> CAM / DENM application messages
        |
        v
Dissemination + duplicate filtering + TTL + forwarding
        |
        v
NR-V2X sidelink abstraction
        |
        +--> Mode-2 style sensing/resource selection
        +--> resource pool
        +--> RSRP estimate
        +--> path loss
        +--> interference
        +--> SINR
        +--> MCS / BLER abstraction
        +--> packet success/failure
        |
        v
Metrics + GUI

## Research basis

Primary architecture reference:
- Castañeda Garcia et al., "A Tutorial on 5G NR V2X Communications",
  IEEE Communications Surveys & Tutorials, 2021.
  DOI: 10.1109/COMST.2021.3057017
  https://ieeexplore.ieee.org/document/9345798/
  Open version: https://arxiv.org/abs/2102.04538

Resource allocation reference:
- Tabassum & Oliveira, "5G NR sidelink time domain based resource allocation in C-V2X",
  Vehicular Communications, Vol. 53, 2025, 100902.
  DOI: 10.1016/j.vehcom.2025.100902
  https://www.sciencedirect.com/science/article/pii/S2214209625000294

Collision/resource-selection reference:
- Tabassum & Oliveira, "Collision Probabilities Between User Equipment Using
  5G NR Sidelink Time-Domain-Based Resource Allocation in C-V2X",
  Electronics, 2025, 14(4), 751.
  DOI: 10.3390/electronics14040751
  https://www.mdpi.com/2079-9292/14/4/751

Standards references:
- 3GPP TS 38.321 (NR MAC; sidelink procedures/resource allocation)
- 3GPP TS 38.211 (NR physical channels/modulation)
- 3GPP TS 38.214 (NR physical-layer procedures)
- 3GPP TS 38.331 (RRC)

Important: this code is an educational/research simulator. It deliberately abstracts the PHY rather than pretending to be a full 3GPP stack.

## Run

Windows:
    py -3.11 main.py

or:
    C:\Users\<you>\AppData\Local\Programs\Python\Python311\python.exe main.py

Python 3.14 should also work because the GUI uses tkinter only. No pygame is required.

## GUI

The GUI lets you:
- add/remove vehicles
- edit position/speed/acceleration/heading
- change communication range
- generate CAM
- generate DENM hazards
- change TTL
- enable/disable forwarding and duplicate filtering
- change CAM interval
- change channel capacity / resource pool size
- inspect SINR, RSRP, MCS, BLER and packet outcomes
- run the simulation dynamically
- inspect PDR, latency, forwarding count, duplicate ratio, TTL drops,
  expiry drops, average neighbors and channel load

## SUMO

SUMO is optional. `sumo_adapter.py` provides a small TraCI adapter. If SUMO
and TraCI are installed, a SUMO vehicle can be mapped into this simulator.
The core application still works without SUMO.

## Hardware path

The code is intentionally layered:

    V2XApplication
        -> DisseminationManager
        -> NRV2XSidelink
        -> RadioModel

For real hardware, replace `NRV2XSidelink` with a backend that talks to a
real PC5-capable modem/UE. The simulator's message/application and metrics
interfaces can remain.

## Evaluation

The included test bench is designed around measurable experiments:
1. sparse vs dense traffic
2. low vs high channel load
3. different resource pool sizes
4. different CAM rates
5. different transmit powers
6. different path-loss/interference settings
7. direct vs multi-hop DENM
8. forwarding on/off
9. duplicate filtering on/off
10. TTL sensitivity

Run:
    py -3.11 test_simulation.py

The script prints a reproducible scorecard.
