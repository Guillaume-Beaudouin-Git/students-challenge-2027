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
