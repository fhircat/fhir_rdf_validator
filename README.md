# FHIR RDF Validation Toolkit
Validate an RDF file or directory containing RDF (in turtle format) against the expected FHIR Schema

## Usage
This package can be used to validate a single RDF file or a directory containing RDF (turtle) files using:
* ShEx - FHIR Shape Expressions definitions of resources and/or
* RDF - Compare two RDF files or directories

```
validate --help
usage: validate [-h] [-i [INFILE [INFILE ...]]] [-id INDIR]
                   [-o [OUTFILE [OUTFILE ...]]] [-od OUTDIR] [-f] [-s]
                   [--shex] [-sd SHEXDIR] [-cd CACHEDIR]

Validate FHIR RDF

optional arguments:
  -h, --help            show this help message and exit
  -i [INFILE [INFILE ...]], --infile [INFILE [INFILE ...]]
                        Input file(s)
  -id INDIR, --indir INDIR
                        Input directory
  -o [OUTFILE [OUTFILE ...]], --outfile [OUTFILE [OUTFILE ...]]
                        Output file(s)
  -od OUTDIR, --outdir OUTDIR
                        Output directory
  -f, --flatten         Flatten output directory
  -s, --stoponerror     Stop on processing error
  --shex                Do ShEx validaton
  -sd SHEXDIR, --shexdir SHEXDIR
                        Base directory of ShEx definitions. Default: indir
  -cd CACHEDIR, --cachedir CACHEDIR
                        Cache directory for cached ShEx
```

## Recommended use
1) Check out, unzip or otherwise create a FHIR `publish` directory, which contains RDF (.ttl) and ShEx (.shex) FHIR
files.
2) Run `validate -id <fhir directory> --sd <fhir directory> --shex -od <other comparison directory> -cd cache`

Note that the run can take a long time if doing ShEx validation and the cache directory hasn't been loaded.


## Notes
1) The PyShEx parser takes a _long_ time to parse the FHIR ShEx Schema definitions.  For this reason, you can specify
a cache directory that carries the parsed (ShExJ) representation of the schemas.  The cache directory that is a part
of this project currently contains a fairly recent version of the FHIR R5 build.
