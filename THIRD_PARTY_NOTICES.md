# Third party notices

FlyReflex original code uses Apache-2.0 (see LICENSE). This does not replace
third-party licenses.

## Three.js

Version 0.186.0, copyright 2010–2026 three.js authors, MIT License.
Installed through the locked npm dependency in web/package-lock.json.
The complete MIT notice is provided in node_modules/three/LICENSE by npm
and must accompany any redistributed bundled Three.js code.
Source: https://github.com/mrdoob/three.js

## MaleCNS

MaleCNS v1.0 data: FlyEM (HHMI Janelia), University of Cambridge Department
of Zoology, MRC Laboratory of Molecular Biology, and Google Research.
Source: https://male-cns.janelia.org/download/
License: Creative Commons Attribution 4.0 International,
https://creativecommons.org/licenses/by/4.0/

FlyReflex selects LPLC2/LC4 → DNp01 direct edges, aggregates their counts,
and normalizes the two totals. These transformations do not imply endorsement
or biologically measured synaptic efficacy. Raw response, query time and
transformation are recorded in data/connectome and docs/DATA_PROVENANCE.md.
Scientific citations are listed in docs/SCIENTIFIC_BASIS.md.

## Other resources

Python runtime helpers use the standard library. Browser fonts are system
fonts; no proprietary font files are redistributed. Scene geometry and SVG
figures are authored in this project. openvela/LVGL and toolchain components
remain in their upstream repositories under their respective licenses.
