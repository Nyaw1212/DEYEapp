# Local Deye logger research

## Confirmed from user's local tests (November 2026)

- The Deye DL1000B-WIFI logger's local web interface is reachable at an address assigned by the user's router.
- The interface shows firmware `DYDA_WiBLE_1.7.2` and indicates a cloud connection.
- HTTP GET serves `/index.html` and `/js/index.js`.
- A TCP port check found HTTP/80 open while TCP/443, 502, 8899, 10000 and 10001 did not accept connections.
- `/js/index.js` defines a navigation map: `status`, `wireless`, `advanced`, `lan`, `network`, `ota`; it sets iframe source to `pageName + '.html'`.
- `index.js` doesn't directly reference `.cgi` endpoints. Other page scripts may do so.
- `curl -I` returned an empty reply; GET succeeded. A rejected HEAD request does not invalidate GET support.

## Not yet established
- Whether this firmware exposes PV watts, battery SOC, home consumption or grid power over HTTP.
- Whether a proprietary local UDP/TCP protocol is available.
- Whether Modbus RTU via a separate RS485 adapter will be necessary.

## Research safeguards
- Use read-only HTTP GET to collect static resources.
- Never send guessed requests to configuration, OTA, write or control endpoints.
- Do not publish credentials, login URLs, tokens, serial numbers, screenshots with account details or Wi-Fi settings.
- Do not assume a logger administration endpoint supports live telemetry.
