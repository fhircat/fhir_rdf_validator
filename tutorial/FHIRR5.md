# Converting vanilla JSON to FHIR RDF
See: https://github.com/fhircat/FHIRCat/issues/2 for additional information

## Conversion to FHIR R5 "minimal"
This is the set of transformations that can be done using only a JSON-LD Context, although we
have also recorded transformations that can be accomplished via the [framing API].

{
   "resourceType": "Patient",
   "id": "Patient/f001"
   "status": "final" .
   "_status": {"id": "y"},
   "state": {"app": 17, "@id": "x"},
   
    "_state": {"id": "x"},
    
    "_state": {"id": "#x"},
 
    "state": {"x": 17, "id": "i"}
  
:s fhir:state :s#x.
:s#x fhir:app 17.
    
http://fhir.org/server/Patient/f001 fhir:status "final".
http://fhir.org/server/Patient/f001# fhir:x 17.

    
inst."x"


"foo2": 
"_foo2": 

:s :foo2  ?v .
:s fhir:extension [...] .



1) **RDF namespace prefixes**

   The list below carries  current set of RDF namespaces that are used by at least one FHIR resource.  
  
   @context: {
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"fhir": "http://hl7.org/fhir/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"owl": "http://www.w3.org/2002/07/owl#",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"xsd": "http://www.w3.org/2001/XMLSchema#",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"dc": "http://purl.org/dc/elements/1.1/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"cs": "http://hl7.org/orim/codesystem/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"dc": "http://purl.org/dc/elements/1.1/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"dcterms": "http://purl.org/dc/terms/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"dt": "http://hl7.org/orim/datatype/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"ex": "http://hl7.org/fhir/StructureDefinition/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"fhir-vs": "http://hl7.org/fhir/ValueSet/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"loinc": "http://loinc.org/rdf#",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"os": "http://open-services.net/ns/core#",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"rim": "http://hl7.org/orim/class/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"rim": "http://hl7.org/owl/rim/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"sct": "http://snomed.info/id/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"vs": "http://hl7.org/orim/valueset/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"w5": "http://hl7.org/fhir/w5#",
    
   **TODO:** This list will continue to expand as new code systems and other things are added to FHIR.  We need to
    develop a mechanism ([prefixcommons](https://github.com/prefixcommons)?, CTS2 service?) to maintain them.  For the
    time being, we've added them to our [current context directory](https://github.com/fhircat/jsonld_context_files/tree/master/contextFiles/root.context.jsonld)
    
2) **resource subject**

   JSON: 
   ```
      "resourceType": "Patient",
      "id": "pat4",
   ```
   
   R4 JSON: 
   ```
       "resourceType" : "Patient",
       "id": {"value": "pat4"},
       "@id": "Patient/pat4",
   ```
   
   RDF:
   ```
       <(server root)/Patient/pat4 fhir:Resource.id ["value": "pat4"] .
   ```

   The subject of a FHIR resource is derived from the resource `"id"`.  According to http://build.fhir.org/resource.html#id :
   
       "The location of a resource instance is an absolute URI constructed from the server base address at which the 
       instance is found, the resource type and the Logical ID, such as http://test.fhir.org/rest/Patient/123 
       (where 123 is the Logical Id of a Patient resource)"
   
   It should be noted that one can add a `"@base": "<fhir server base>"` to the context to make this resolve correctly
   
   **[resource subject Example](http://tinyurl.com/sgc7boc)**
   
3) **resource type**

   JSON: 
    
    ```
       "resourceType": "Patient"
    ```
   R4 JSON: 
   ```
       "resourceType" : "fhir:Patient",
          ...
       "@context": [
           "https://raw.githubusercontent.com/fhircat/jsonld_context_files/master/contextFiles/patient.context.jsonld",
           "https://raw.githubusercontent.com/fhircat/jsonld_context_files/master/contextFiles/root.context.jsonld",
          {"@base": "http://build.fhir.org/"}]
            
   ```
    
    CONTEXT:
    ```
      "resourceType": {
        "@id": "rdf:type",
        "@type": "@id"
      },
    ```
    RDF: 
    ```
    <subject URI> a <http://hl7.org/fhir/Patient> .
    ```
 
    **[resource type example](http://tinyurl.com/uc7dwnp)**
    
4) **tree root**

    We need to add an indicator to all resources to identify where they should be framed.
    
    R4 JSON: 
   ```
       "fhir:nodeRole" : "fhir:treeRoot",
   ```

    RDF: 
    
    ```text
    <subject URI> fhir:nodeRole fhir:treeRoot .
    ```
    
    @context:
    
    _framing_: `"resourceType": {},`
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; `"nodeRole": {"@default": "http://hl7.org/fhir/treeRoot"},`
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; `"@requireAll": true`
    
    Note: We might consider replacing the wild card on `resourceType` with a complete list of resources: `["Patient", "Account", ...]`
   
   **[tree root example](http://tinyurl.com/wcjaqgr)**

5) **primitive values**
    
    With the exceptions listed below, all FHIR primitive types have to be converted to a JSON object with a `"value` 
    element:
    1) elements that begin with '@' (json-ld instructions)
    2) objects and lists -- although they do have to be processed recursively
    3) `"id"` elements -- these become the subjects of their container
    4) '"resourceType", "nodeRole", "index", "div' elements
    
    JSON: 
        
    ```
       "(key)": "(val)"
    ```
   R4 JSON: 
   ```
       "(key)" : {"fhir:value": "(val)},

   ```    
    
6) **list ordering**
 
    JSON lists are ordered.  JSON-LD lists are not, so it is necessary to add an ordering index to list elements.
   
    _**Question**_: Is it possible to have a list within a list in FHIR (e.g. `"foo": [["bar": 17, ...], ...])`?
    
    For each _object_ within a list, add a relative index:
    
    R4 JSON
    ```json
    {
        "telecom": [
        {
          "index": 0,
          "use": "home"
        },
        {
           "index": 1,
          "system": "phone",
          "value": "(03) 5555 6473",
          "use": "work",
          "rank": 1
        },
        {
           "index": 2,
          "system": "phone",
          "value": "(03) 3410 5613",
          "use": "mobile",
          "rank": 2
        },
        {
          "index": 3,
          "system": "phone",
          "value": "(03) 5555 8834",
          "use": "old",
          "period": {
            "end": "2014"
          }
        }
      ]
   }
   ```
   
   Note that lists may be (indirectly) nested within other lists

6) **References**
    FHIR references require two additions:
   
   1) The [Reference](http://build.fhir.org/references.html#Reference) data type includes the `reference` attribute, a "Literal reference, Relative, 
   internal or absolute URL".  If this is a relative reference, it is relative to the _parent_ of the resource, not the
   resource itself.  As an example, if the resource at the URL `https://fhirserver.org/Observation/o12345` contains a reference
   to `"Patient/P1111`, the full URI reference would be `"https://fhirserver.org/Patient/P1111"` instead of 
   `"https://fhirserver.org/Observation/Patient/P1111"`, which is what you would get with a normal web page.  As a 
   consequence, ".." needs to be prepended to any _relative_ `Reference.reference` entry.  Example:
   
   ```json
     "subject": {
       "reference": "Patient/f001",
       "display": "P. van de Heuvel"
      }
    ``` 
   Becomes:
   ```json
     "subject": {
       "fhir:link": {"@id": "../Patient/f001"},
       "reference": "Patient/f001",
       "display": "P. van de Heuvel"
      }
    ``` 
   
   The R4 specification also adds a "type arc", in the form:
   ```text
   <http://hl7.org/fhir/Patient/f001> a fhir:Patient .
   ```
   If the type of the reference can be determined.  Since the R4 RDF specification was published, a new (albeit optional)
   field was added to the `Reference` type, `type`, which (while specified as a URI?) identifies the FHIR data type.  To
   completely match the R4 specification, and _if_ there is a `reference` attribute the pre-processor needs to insert 
   the `link` arc:
    ```json
    "subject": {
       "reference": "Patient/f001",
       "display": "P. van de Heuvel",
       "link": {
          "@id": "../Patient/f001",
          "@type": "Patient"
       }   
    }
    ``` 
   where the `"@id"` is the `reference` with a '..' prepended if it is relative, and the type is the `"type"` field if
   it is present and, if not, if the URL matches the recommended FHIR Regexp (to be supplied), the resource type from
   there, otherwise, omit it.

        
3) **RDF data types**

    All non-string values need to have a corresponding RDF datatype inserted.  This requires access to the 
    FHIR metamodel, as the JSON itself does not have sufficient typing information.
    
    1) **Case 1:** value has an explicit type - see: http://build.fhir.org/datatypes.html#Period for an example, where both
       the start and end nodes are of the _FHIR_ type `dateTime`. The current R4 type map can be found in 
       [RDFTypeMap.java](https://github.com/HL7/fhir/blob/master/implementations/java/org.hl7.fhir.rdf/src/org/hl7/fhir/rdf/RDFTypeMap.java).
       
    2) **Case 2:** variable value type - the datatype is encoded onto the end of the variable name.  This can be identified
       in the FHIR metamodel, and is represented as `<tag>[x]` where `x` is the actual datatype (e.g. `valueBoolean`, 
       `valueDateTime`, etc.) The data type has to be parsed from the key and then mapped as with Case 1 above.
       
4) **ID and extension transformation for primitive types**
    
    FHIR primitive types derive from [Element](http://build.fhir.org/types.html#Element), meaning that _any_ data element
    can have an `id` and/or `extension`.  The FHIR JSON rendering keeps underlying data "primitive" (i.e. represented as
    a value, not a JSON Object), but uses a lexical convention to associate the base element with the additional attributes.
    The JSON will prepend an underscore ('_') to the key name with an object that contains the `id` and/or `extension`.
    
    Whenever you encounter a tag with an underscore, locate the corresponding tag without the underscore and merge the 
    contents of the underscored object with the contents of the basic tag (which will already _be_ an object from step 1:
    
    ```json
   {
    "birthDate": "1970-03-30",
     "_birthDate": {
       "id": "314159",
       "extension" : [ {
          "url" : "http://example.org/fhir/StructureDefinition/text",
          "valueString" : "Easter 1970"
       }]
     }
   }
   ```
   Step 1:
   ```json
   {
    "birthDate": {"value": "1970-03-30"},
     "_birthDate": {
       "id": {"value": "314159"},
       "extension" : [ {
          "url" : {"value": "http://example.org/fhir/StructureDefinition/text"},
          "valueString" : {"value": "Easter 1970"}
       }]
     }
   }
   ```
    Step 2:
   ```json
   {
    "birthDate": {"value": "1970-03-30", "@type": "xsd:dateTime"},
     "_birthDate": {
       "id": {"value": "314159"},
       "extension" : [ {
          "url" : {"value": "http://example.org/fhir/StructureDefinition/text", "@type":  "xsd:anyURI"},
          "valueString" : {"value": "Easter 1970"}
       }]
     }
   }
   ```
    And finally:
   ```json
   {
    "birthDate": {
      "value": "1970-03-30", 
      "@type": "xsd:dateTime",
       "id": {"value": "314159"},
       "extension" : [ {
          "url" : {"value": "http://example.org/fhir/StructureDefinition/text", "@type":  "xsd:anyURI"},
          "valueString" : {"value": "Easter 1970"}
       }]
     }
   }
   ```  
      

   
5) **Concept References**
    
    FHIR uses the composite [Coding](http://build.fhir.org/datatypes.html#Coding) datatype to reference a concept identifier.
    A key element of the RDF implementation is the notion of concept URI's.  Where _possible_, we need generate a "type arc"
    for a concept identifier that references a URL. Note that there Were more mappings in our original submission, but the
    current two (with an error in LOINC) can be found at 
    https://github.com/hapifhir/org.hl7.fhir.core/blob/master/org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/formats/RdfParserBase.java

   
   See: http://tinyurl.com/s6gkyx7 for an example

8) **OWL Ontology Header**

    The OWL Ontology header is often used as a "poor man's" document wrapper in OWL and RDF land.  It asserts provenance
    for the set of triples that occur in the same physical document as the header itself.  The following should be added
    to every JSON resource to generate the header:
    
    R4 JSON
    ```json
      "@included": {
         "@id": "Observation/f001.ttl",
         "@type": "owl:Ontology,"
         "owl:imports": "fhir:fhir.ttl",
         "owl:versionIRI": "Observation/f001.ttl"
      }
    ```
   
   CONTEXT
   ```json
    "owl:versionIRI": {"@type": "@id"},
    "owl:imports": {"@type": "@id"},
   ```
   
   [Ontology Header Example](http://tinyurl.com/sacszom)
   
   
   
----------
Old material

    
   The FHIR R4 RDF specification _adds_ the type field, meaning that it is necessary to add an attribute to the core
   JSON:
   
        `"@id": "<resourceType>/<id>"
   
   
   A FHIR resource references its subject via the `"id"` key, which will form the URI _relative_ to the document base.
   
   _**TODO:**_ We need to establish whether the `"id"` tag is used for anything _but_ identifiers.  If it is, we will
   either a) identify these situations and disable the default processing or b) change `"id"` to `"@id"` in the JSON
   preprocessor.  An example of a) would be:
   
   ```"@context": {
         "id": "@id",
            ...
         "someReference": {
            "id": null
         },
   ```
   {
     "id": "Patient/f001",
     "name": "fred",
     "something": {
        ""
        "id": {"advice" : "Take drugs"}
        
:Patient/f001 fhir:name "fred";
              fhir:something {
                 ""
   JSON: `"id": "<relative or absolute URI>"`
   <br/>RDF: `<subject URI> a <resourceType>`
   
   @context: 
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;`"id" : "@id",`
    
    **[Example](http://tinyurl.com/spex7s8)**
    
    _**Note:**_ https://github.com/fhircat/FHIRCat/issues/2 indicates that we need to escape inner `id`'s -- it isn't obvious
    why this is the case.  Needs further discussion...