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

## Second token, the same evening

Five entries, after a change of roles in the team and a review of entry 005:
`LOGBOOK_2026-11-24_v2.tsr`, for the manifest as it stood then.

```
SHA-256  b3fe05e705e340e144fa6f0f75ba71af6bab3c1cd848d26cba1d9bfb00d0c2c9
Time     24 November 2026, 22:33:51 GMT
Serial   0x34488B6C69E58BC7A946EA922B6DD245
```

```bash
cd logbook && shasum -a 256 -c MANIFEST.sha256 && cd ..
openssl ts -verify -data logbook/MANIFEST.sha256 -in timestamps/LOGBOOK_2026-11-24_v2.tsr -CAfile /etc/ssl/cert.pem
```

The first token covers the four entries as first published (commit `74002b0`).

## Third token: entry 005 reworded

`LOGBOOK_2026-11-24_v3.tsr`, after the logic of entry 005 was reworded (a review found it too binary).

```
SHA-256  4590504bf888125dc820a2e4bb0c1c115c3c698270eb08e1724e5634d3d6262f
Time     Nov 24 22:54:57 2026 GMT
Serial   0xE797E64890D5CBB7EE331C95A9250E05
```

## Fourth token: definitions added to entry 005

`LOGBOOK_2026-11-25_v4.tsr`: entry 005 now defines capital expenditure and net borrowing, with the
figure for each company.

```
SHA-256  3327e7bef7dfba7c009df6e11ab19b6ef26feec649ff637e19fbc8b2d5b09d26
Time     Nov 24 23:26:43 2026 GMT
Serial   0xB3F078F0E53F58EAB8AE47F1DEBE9CA0
```

## Fifth token: entries 002 and 005 after a fourth outside review

`LOGBOOK_2026-11-25_v5.tsr`. Entry 002: free cash flow is now taken from the companies' cash-flow
statements for the three candidates, valued on the same day, and the entry says what the earlier
version got wrong. Entry 005: five definitions added (the six, "six times", eight and three, what
the figures measure, the yield sensitivity); no figure of the entry has changed.

```
SHA-256  d8d53737b11b8cf679a8806c5e00cca17c53d5218f4296a21996ccf0d8e16224
Time     Nov 25 00:07:07 2026 GMT
Serial   0x5F2A944461444D597A7290CF2A99765E
```

## Sixth token: entry 002, margin, debt and one answer

`LOGBOOK_2026-11-25_v6.tsr`. Entry 002: the operating margin and the debt ratio are now those of
the company's statements (18.0%; under 2 times EBITDA, with both readings given), and the answer to
the objection quotes how the share has moved against the six since 2023. Printed by
`descriptive/stock_example.py` and `descriptive/the_bet.py`.

```
SHA-256  dd9a6a4ef11f6d412acde3d5f37ccffd56272545a47dda55652aefe6b7b9bb6b
Time     Nov 25 00:14:32 2026 GMT
Serial   0x671061984C5686435A6A64A18946691F
```

## Seventh token: the five entries voted

`LOGBOOK_2026-11-25_v7.tsr`. The status of each entry goes from "Proposal, not yet voted" to the
result of the vote: six for, none against, given in writing by each member and recorded by the
chair on 25 November 2026. Nothing else changes in the entries.

```
SHA-256  70713d1a185fc6febde1f0919bacd3e77142a551fe7b75b21c1a6e4325605bc6
Time     Nov 25 01:02:54 2026 GMT
Serial   0x2C8E837CB1C08E6A1A852ABDB9994155
```

## Eighth token: two wordings aligned with the application file

`LOGBOOK_2026-11-25_v8.tsr`. The status line of each entry now reads "Voted on by the six of us",
and entry 005 says the market "has hit the sellers far harder than the buyers", as the file sent to
Natixis does. No figure, date or decision has changed.

```
SHA-256  cd44088b3c6f3d327bbbd55f634ff3e6d8f2d710be9a54a0db07e8b27f592744
Time     Nov 25 03:19:28 2026 GMT
Serial   0x2A6ED4DFB717B672B3A5756EED6BF15D
```
