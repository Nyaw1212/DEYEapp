# DEYEapp

Windows desktop monitoring project for a Deye hybrid inverter, starting with read-only local logger research.

## Hardware under investigation
- Inverter: Deye SUN-6K-SG05LP1-EU-AM2-P (6 kW)
- Wi-Fi logger: Deye DL1000B-WIFI, firmware observed: DYDA_WiBLE_1.7.2
- Local logger: user-configurable IP; **never put credentials in this repository**

## Current findings
- Logger has an HTTP interface on port 80.
- Ports 502 and 8899 did not accept TCP connections during initial tests.
- The logger's `index.js` loads pages through `<page>.html`, including `status.html`.
- Read-only, near-real-time power telemetry has **not yet** been established.
- Cloud dashboard freshness depends on upstream logger/cloud reporting.

## Next step: Collect scripts for offline review

On a Windows PC connected to the same trusted network as the logger:

```powershell
git clone https://github.com/Nyaw1212/DEYEapp.git
cd DEYEapp
powershell -ExecutionPolicy Bypass -File .\scripts\collect-logger-pages.ps1 -LoggerIP 192.168.1.93
```

The script fetches only HTML/JavaScript/CSS using HTTP GET, performs no login, and saves results locally in `logger_research/`. **Review and redact downloaded files before committing or sharing**; device pages may contain serial numbers or other sensitive metadata.

## Intended development stages
1. Verify the device's documented or observed read-only telemetry interface.
2. Implement a local data collector with timeouts, error handling and a configurable refresh interval.
3. Build a Windows desktop widget for PV, load, battery and grid power.
4. Package as a Windows application after hardware testing.

See `docs/RESEARCH.md` for the known observations and constraints.
