# Pocketso visual identity

Pocketso uses a compact, portable-drive silhouette as its text/terminal mark. The Fastfetch profile uses the actual `fastfetch` program and reads its ASCII logo from:

`/usr/share/pocketso/fastfetch/pocketso.txt`

The configuration is installed for the live Pocketso account and copied to the installed USB user's Fastfetch config.

## Core palette

| Use | Color | Hex |
| --- | --- | --- |
| Main Pocketso accent | Green | `#A5E65A` |
| Dark body / device | Black | `#111411` |
| Device edge / secondary text | Grey | `#858D86` |
| USB 2.0 speed marker | White | `#F4F5F2` |
| USB 3.x speed marker | Blue | `#2684E8` |
| USB4 speed marker (v1/v2) | Violet | `#9B75E8` |

Violet is the Pocketso USB4 marker: it is distinct from USB 3.x blue while still reading as a high-bandwidth, next-generation interface. These are visual labels only; software must identify a device's actual negotiated USB speed before showing a speed marker.

## Fastfetch

The logo is plain ASCII, not an SVG. Fastfetch remains a real installed package; the custom text file is only its logo source. The profile shows Pocketso's green and white identity in terminal output while the device drawing uses a restrained black/grey outline.
