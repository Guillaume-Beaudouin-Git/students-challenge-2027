# Independent time-stamp of the pre-registration

`PREREGISTRATION.tsr` is an RFC 3161 time-stamp token issued by DigiCert's public
time-stamping authority for the SHA-256 fingerprint of `PREREGISTRATION.md`:

```
SHA-256  1bc296c43b7a76bebba9e302202f28cd6ddb8922dc4f31a04686dc3a90fd003e
Time     24 November 2026, 17:57:05 GMT
Serial   0xF5311D622BCC0DC147ED1C031E61CE3A
```

Only the fingerprint was sent, not the file. A commit date can be rewritten; this token
cannot be produced after the fact. To check it:

```bash
shasum -a 256 PREREGISTRATION.md
openssl ts -reply -in timestamps/PREREGISTRATION.tsr -text
openssl ts -verify -data PREREGISTRATION.md -in timestamps/PREREGISTRATION.tsr -CAfile /etc/ssl/cert.pem
```

The last command prints `Verification: OK` only if the file is byte-for-byte the one that
was time-stamped.

# Independent time-stamp of the Logbook entries

`LOGBOOK_2026-11-24.tsr` is a token from the same authority for the SHA-256 fingerprint of
[`../logbook/MANIFEST.sha256`](../logbook/MANIFEST.sha256), which lists the fingerprint of each
entry as it stood that evening:

```
SHA-256  15ef8c94336163d0d092a53896bbcca484952eb163270b17976c6c37363008bf
Time     24 November 2026, 21:40:13 GMT
Serial   0x4982D570E1B17037187F2790A6DE3DFC
```

To check it:

```bash
cd logbook && shasum -a 256 -c MANIFEST.sha256 && cd ..
openssl ts -verify -data logbook/MANIFEST.sha256 -in timestamps/LOGBOOK_2026-11-24.tsr -CAfile /etc/ssl/cert.pem
```

An entry that changes later gets a new manifest and a new token; the old ones stay in the history
of the repository.
