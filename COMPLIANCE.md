# AGPL-3.0 Compliance Guide

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

## For Maintainers

- Include the full AGPL-3.0 text in the repo root as `LICENSE`
- Keep a `NOTICE` file and Third-Party notices (see `docs/LICENSE.md`)
- Tag releases; publish source matching any distributed binaries/containers
- Ensure the UI exposes a "Source" link to the exact commit/tag of the running build (Section 13)

## For Distributions (devices/containers)

- Provide corresponding source for each shipped version:
  - Application source code and build/install scripts (e.g., Dockerfiles)
  - Third-party licenses and notices included in images
- If distributing to end users (potential "User Products" under GPLv3):
  - Provide installation information sufficient for users to install modified software

## Network Use (AGPL Section 13)

- If users interact with the Designer UI or APIs over a network, provide access to the corresponding source of the running version
  - Add a "Source" link in the UI footer/menu pointing to the specific commit/tag

## Third-Party Licenses

- Retain all upstream license texts and notices in distributions
- BACnet libraries:
  - BAC0 (GPL-3.0): combining/distributing with BAC0 enforces GPL/AGPL copyleft on the combined work
  - bacpypes3 (MIT): permissive; include MIT notice

## Patents

- AGPL-3.0 includes an explicit patent license and retaliation clause (Section 11)

## Questions

- For questions about compliance, open an issue or contact the maintainers
