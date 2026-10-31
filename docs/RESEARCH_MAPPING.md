# Research-to-Code Mapping

| Project component | Code | Research/standard basis |
|---|---|---|
| NR-V2X sidelink architecture | network.py | Castañeda Garcia et al., IEEE COMST 2021 |
| Mode-2 resource selection abstraction | resource_manager.py | Castañeda Garcia et al.; 2025 Vehicular Communications paper |
| Resource collision modeling | resource_manager.py + radio.py | 2025 Electronics collision-probability paper |
| PC5/direct V2V abstraction | network.py | NR-V2X sidelink architecture |
| CAM/DENM application | models.py | ETSI/ITS message concepts; application layer |
| TTL/duplicate filtering | dissemination.py | V2X dissemination baseline; project design |
| DCC abstraction | dcc.py | project-level congestion-control abstraction |
| SINR/BLER/MCS system model | radio.py | system-level radio abstraction |
| Mobility | models.py / sumo_adapter.py | simulation layer |
| Security hook | network.py boundary | reserved for teammate's security/trust module |
| Metrics | metrics.py | V2X evaluation methodology |

## Critical distinction

The project references research papers, but not every line of code is directly
"implemented from a paper". Research papers motivate architecture and algorithms;
3GPP specifications define normative protocol behavior.

For a capstone report, label the implementation as:
"research-oriented system-level NR-V2X sidelink simulation"
rather than "3GPP-compliant NR-V2X modem".
