# Experimental local Python client

**Unverified on the actual DL1000B-WIFI logger.** The protocol is inferred from downloaded JavaScript. This is not a live-power dashboard yet.

## Install and run (PowerShell)

```powershell
cd $HOME\Desktop\DEYEapp
git pull
py -m pip install -r requirements.txt
py .\deye_local.py --ip 192.168.1.93
```

The script performs GET requests only, to the encoded forms of `require.cgi`, `send.cgi`, and `status.cgi`. It never calls control, configuration or OTA endpoints. A key exchange does modify the logger's temporary session encryption state, so avoid simultaneous local-web sessions while testing.

The firmware's `encrypt_rsa()` wrapper has not yet been verified; the prototype assumes the standard JSEncrypt RSA PKCS#1 v1.5 encryption with Base64 output. If key exchange fails, inspect that wrapper rather than trying arbitrary endpoints.

**Privacy:** Do not paste raw status responses, session keys, RSA private keys, serial numbers, Wi-Fi credentials or authentication cookies into public issues or commits. The client prints only field names and a limited set of scalar power/yield values. The logger's status endpoint may not expose battery SOC, load or grid power.

## Troubleshooting
- Empty response: verify that the browser's normal local status page works; another session may have changed the AES key.
- Invalid RSA key: inspect the `require.cgi` response format locally.
- Key exchange failed: verify `encrypt_rsa()` in the firmware and URL encoding.
- Unexpected JSON: inspect locally and redact before sharing.
