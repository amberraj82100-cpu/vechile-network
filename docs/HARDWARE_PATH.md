# Hardware Integration Path

## Simulation
Python + this simulator.

## HIL
Replace:
    NRV2XSidelink
with an adapter to a hardware/SDK interface.

The application layer can remain:
    CAM/DENM -> DisseminationManager -> V2X backend

## Real vehicle stack

Potential real interfaces:
- GNSS for position/time
- CAN/CAN-FD for vehicle state
- Ethernet/USB to V2X modem
- PC5-capable NR-V2X UE/modem
- onboard computer for application logic

The exact hardware API is vendor-specific.

## Important
Do not claim that a normal 5G modem provides PC5 sidelink. The hardware must
explicitly support the required NR sidelink/V2X capability and deployment
band/configuration.
