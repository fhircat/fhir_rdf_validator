# Embedded Resource Issue

## Background
There are at least four places where a FHIR resource can be embedded inside another resource:
1) Bundle -- `Bundle.entry.resource` carries arbitrary resources
2) Bundle -- `Bundle.entry.response.outcome`
3) _Any_ Resource -- `DomainResource.contained`
4) Parameters -- `Parameters.parameter.resource`

The existing processing model assumes that the particular context to be used (e.g. `Patient.context.json`) is
determined by the `resourceType` value _before processing begins_.  Unfortunately, there is nothing in the processing 
that allows us to "step aside" to determine which base context is to be used to validate inner resources.  It appears
that we have two choices:

1) Create an "uber context" that references _all_ FHIR Resource contexts and uses a (yet to be determined) aspect of
the JSON-LD 1.1 processor to decide which context applies.
2) Tie the embedded resources to their corresponding contexts in the JSON pre-processing step.

Unless a JSON-LD processor is able to do "lazy loading" of contexts, option 1 would require that a JSON-LD processor
parse _all_ FHIR resource definitions before getting started -- a non-viable option from both load time and memory
utilization perspectives.

## Proposed Approach
The JSON preprocessor needs to locate _every_ resourceType entry and add it to the context header.  As an example,  
http://build.fhir.org/bundle-example.json has an embedded `MedicationRequest` resource.  This needs to be added to 
the header:
```json
{
  "@context": [
    "https://fhircat.org/fhir/contexts/r5/bundle.context.jsonld",
    "https://fhircat.org/fhir/contexts/r5/medicationrequest.context.jsonld",
    "https://fhircat.org/fhir/contexts/r5/root.context.jsonld",
    {
      "@base": "http://hl7.org/fhir/",
      "nodeRole": {
        "@type": "@id",
        "@id": "fhir:nodeRole"
      },
      "owl:imports": {
        "@type": "@id"
      },
      "owl:versionIRI": {
        "@type": "@id"
      }
    }
  ],
  ...
}
```

