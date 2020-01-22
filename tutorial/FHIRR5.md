# Converting vanilla JSON to FHIR R5 Minimal
1) **`fhir`, `rdfs`, `xsd` and `owl` namespaces**
  
   @context:
   <br/>&nbsp;&nbsp; &nbsp; &nbsp;"fhir": "http://hl7.org/fhir/",
   <br/>&nbsp;&nbsp; &nbsp; &nbsp;"owl": "http://www.w3.org/2002/07/owl#",
   <br/>&nbsp;&nbsp; &nbsp; &nbsp;"rdfs": "http://www.w3.org/2000/01/rdf-schema#",
   <br/>&nbsp;&nbsp; &nbsp; &nbsp;"xsd": "http://www.w3.org/2001/XMLSchema#",
2) **resource subject**

   JSON: `"id": "<relative or absolute URI>"`
   <br/>RDF: `<subject URI> a <resourceType>`
   
   @context: 
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;`"id" : "@id",`
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;`"@base : "http://fhirserver.org/"`
    
    **[Example](http://tinyurl.com/spex7s8)**
     
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
    
    _preprocessing_ : add `"nodeRole": "treeRoot"`
    
    _framing_: `"resourceType": {},`
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; `"nodeRole": {"@default": "http://hl7.org/fhir/treeRoot"},`
    <br/>&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; &nbsp; &nbsp;&nbsp;&nbsp; `"@requireAll": true`
    
    Note: We might consider replacing the wild card on `resourceType` with a complete list of resources: `["Patient", "Account", ...]`
   
   **[Example](http://tinyurl.com/qsucv4b)**

5) index on lists

6) concept URI

7) Reference link

Links -- have to stick the ".." in