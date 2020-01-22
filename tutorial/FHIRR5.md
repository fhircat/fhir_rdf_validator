# Converting vanilla JSON to FHIR 
See: https://github.com/fhircat/FHIRCat/issues/2 for additional information

## Conversion to FHIR R5 "minimal"
This is the set of transformations that can be done using only a JSON-LD Context, although we
have also recorded transformations that can be accomplished via the [framing API].

1) ** RDF namespace prefixes **
  
   @context: {
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"fhir": "http://hl7.org/fhir/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"owl": "http://www.w3.org/2002/07/owl#",
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
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"rim": "http://hl7.org/orim/class/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"rim": "http://hl7.org/owl/rim/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"sct": "http://snomed.info/id/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"vs": "http://hl7.org/orim/valueset/",
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;"w5": "http://hl7.org/fhir/w5#",

   
2) **resource subject**
   
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

   JSON: `"id": "<relative or absolute URI>"`
   <br/>RDF: `<subject URI> a <resourceType>`
   
   @context: 
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;`"id" : "@id",`
    
    **[Example](http://tinyurl.com/spex7s8)**
    
    _**Note:**_ https://github.com/fhircat/FHIRCat/issues/2 indicates that we need to escape inner `id`'s -- it isn't obvious
    why this is the case.  Needs further discussion...

3) **resource type**

    JSON: `"resourceType": "Patient"`
    <br/>RDF: `<subject URI> a fhir:Patient .`
    
    @context:
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;`"@vocab": "http://hl7.org/fhir/",`
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;`"resourceType": "@type"`,
    
    **[Example](http://tinyurl.com/spex7s8)** 
    
4) **tree root**

    RDF: `<subject URI> fhir:nodeRole fhir:treeRoot .`
    
    @context:
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;`"fhir:treeRoot": "@id",`
    
    _framing_: `"resourceType": {},`
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; `"nodeRole": {"@default": "http://hl7.org/fhir/treeRoot"},`
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; `"@requireAll": true`
    
    Note: We might consider replacing the wild card on `resourceType` with a complete list of resources: `["Patient", "Account", ...]`
   
   **[Example](http://tinyurl.com/qsucv4b)**



## Additional transformations that are necessary to generat the current R4 ITS
The transformations below need to be done prior to transforming the JSON to JSON-LD.  The examples are drawn from
http://build.fhir.org/patient-example.ttl.html (RDF) and http://build.fhir.org/patient-example.json.html (JSON) unless
otherwise specified.

1) **tree root**

   **Description:** A FHIR resource needs to have an additional triple in the form of:
       
       <subject> fhir:nodeRole fhir:treeRoot.
       
    to allow proper framing.
    
    _preprocessing_ : add `"nodeRole": "treeRoot"` to a resource
    
2) **id base**


2) **non-object nodes**

    **Description:** With the exception of the predicates `"nodeRole"`, `"index"` (in the context of list ordering, 
    type arcs (`rdf:type`) and `"div"` as a child of `"Narrative"`, all non-object / non-list objects need to be 
    converted to an object containing `fhir:value`:
    
        `"<key>" : <value>`  --> `"key": {"value": <value>}.  
        
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
      
4) **list ordering**

    JSON lists are ordered.  JSON-LD lists are not, so it is necessary to add an ordering index to list elements.
   
    _**Question**_: Is it possible to have a list within a list in FHIR (e.g. `"foo": [["bar": 17, ...], ...])`?
    
    For each _object_ within a list, add a relative index:
    
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
   
5) **Concept References**
    
    FHIR uses the composite [Coding](http://build.fhir.org/datatypes.html#Coding) datatype to reference a concept identifier.
    A key element of the RDF implementation is the notion of concept URI's.  Where _possible_, we need generate a "type arc"
    for a concept identifier that references a URL. The current mappings can be found at 
     [RDFTypeMap.java.decorateCoding()](https://github.com/HL7/fhir/blob/master/implementations/java/org.hl7.fhir.rdf/src/org/hl7/fhir/rdf/RDFTypeMap.java#111)
     
6) ** References **
   
   The [Reference](http://build.fhir.org/references.html#Reference) data type includes the `reference` attribute, a "Literal reference, Relative, 
   internal or absolute URL".  If this is a relative reference, it is relative to the _parent_ of the resource, not the
   resource itself.  As an example, if the resource at the URL `https://fhirserver.org/Observation/o12345` contains a reference
   to `"Patient/P1111`, the full URI reference would be `"https://fhirserver.org/Patient/P1111"` instead of 
   `"https://fhirserver.org/Observation/Patient/P1111"`, which is what you would get with a normal web page.  As a 
   consequence, ".." needs to be prepended to any _relative_ `Reference.reference` entry.  Example:
   
   ```json
   { ...
     "subject": {
     "reference": "Patient/f001",
     "display": "P. van de Heuvel"
      },
    ``` 
   Becomes:
   ```json
   { ...
     "subject": {
     "reference": "../Patient/f001",
     "display": "P. van de Heuvel"
      },
    ``` 
   
   The R4 specification also adds a "type arc", in the form:
   ```text
   <http://hl7.org/fhir/Patient/f001> a fhir:Patient .
   ```
   If the type of the reference can be determined.  Since the R4 RDF specification was published, a new (albeit optional)
   field was added to the `Reference` type, `type`, which (while specified as a URI?) identifies the FHIR data type.  To
   completely match the R4 specification, the pre-processor needs to:
   
   1) if `type` is present and it is a relative 

       
   
   
6) **Link properties**

7) **Reference type arcs**

8) **OWL Ontology Header**