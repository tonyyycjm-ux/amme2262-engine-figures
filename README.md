# AMME2262 engine laboratory figures

Python source for the six figures used in the engine report (experiment: 20 October 2026). Figures are calculated and plotted with NumPy, SciPy, pandas and Matplotlib. They are not generated with an image-generation model.

## Run

Use Python 3.10 or later. Supply your own authorised experimental files; the laboratory manual, report and raw measurements are not published here.

```sh
python -m pip install -r requirements.txt
python plot_engine.py --data-dir /path/to/experiment --output-dir outputs
```

The input folder must contain `engine lab.xlsx` (VDAS export) and `engine lab111.XML` (ECA100 export). File names are case-sensitive on some operating systems. The XLSX is read through its standard ZIP/XML contents to avoid its malformed rich-text colour metadata.

## Report figure mapping

| Report figure | Output | Calculation |
| --- | --- | --- |
| 1 | `engine_performance.png` | Torque, power, exhaust temperature, BMEP, air flow and volumetric efficiency |
| 2 | `engine_pressure.png` | Raw pressure against crank angle, relative time and cylinder volume |
| 3 | `cycle_otto.png` | Constant-specific-heat Otto P–V and T–s cycles |
| 4 | `cycle_diesel.png` | Constant-specific-heat Diesel cycles |
| 5 | `cycle_dual.png` | Constant-specific-heat Dual cycles |
| 6 | `cycles_variable.png` | Temperature-dependent specific-heat comparison |

Each figure is saved as a 300 dpi PNG and vector PDF. The script also writes a full operating-history figure, recalculated CSV data, five unwrapped ECA cycle CSV files and model state results.

## Assumptions and limits

- Geometry is taken from the recorded ECA configuration: bore 69 mm, stroke 62 mm and compression ratio 22; it is not an independent dimensional measurement.
- Three representative time windows are 20–60, 100–140 and 180–192 seconds. The last condition remains transient.
- The negative airbox differential is interpreted as suction relative to ambient. No legacy +32767 Pa correction is added.
- The cylinder-pressure floor of −30 is retained. No signal offset or synthetic measurement is substituted. Fuel-derived efficiency is unsuitable where the recorded input produces values above 100%.
- Constant-specific-heat cycles match brake work by construction. This does not validate indicated pressure or heat release. The Dual model assumes a 50/50 heat-input split.
- The variable-specific-heat comparison holds the original heat input fixed. Ideal air is represented by 79% N2 and 21% O2 by mole, using NIST Shomate coefficients.

## Checks

The script checks all 18 model cases for positive net work, entropy closure and agreement between numerical P–V integration and the heat balance (relative tolerance 0.2%). Nine constant-specific-heat models must reproduce their specified brake-output targets. These checks verify numerical consistency, not experimental calibration.

## Property sources

- [NIST Nitrogen Shomate data](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1)
- [NIST Oxygen Shomate data](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7782447&Mask=1)

AI assistance: OpenAI Codex assisted with the analysis implementation, plotting and documentation. The code and interpretation require the report authors' review.
