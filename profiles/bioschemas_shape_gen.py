from rdflib import ConjunctiveGraph, URIRef
from rdflib.namespace import RDF
from jinja2 import Template
from pyshacl import validate

import os
from os import walk
import json

from metrics.WebResource import WebResource


class BioschemasProfileError(Exception):
    def __init__(self, class_name, message="The profile is yet defined"):
        self.class_name = class_name
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.class_name} -> {self.message}"


def generate_profiles_from_files():
    profile_files = []

    # get list of path of .json bioschemas profiles
    dir_path = os.path.join(os.path.dirname(__file__), "../data/specifications")
    for (sub_dir_path, dirnames, filenames) in walk(dir_path):
        # print(dirnames)

        for (dirpath, dirnames, filenames) in walk(sub_dir_path):
            for filename in filenames:
                if filename.endswith("RELEASE.json"):
                    profile_files.append(dirpath + "/" + filename)
                    # print(dirpath + "/" + filename)
        break

    bs_profiles = {}

    # retrieve and parse content of .json profiles files
    for profile_file in profile_files:

        with open(profile_file) as f:
            profile = json.load(f)

            bs_id = profile["@graph"][0]["@id"]
            bs_profiles[bs_id] = {"min_props": [], "rec_props": []}

            for g in profile["@graph"]:
                if ("$validation") in g.keys():
                    for k in g["$validation"]["required"]:
                        bs_profiles[bs_id]["min_props"].append("schema:" + k)
                    if "recommended" in g["$validation"].keys():
                        for k in g["$validation"]["recommended"]:
                            bs_profiles[bs_id]["rec_props"].append("schema:" + k)
    return bs_profiles


def gen_shacl_alternatives(bs_profiles):
    res = {}
    for p in bs_profiles.keys():
        res[p] = {}
        min = []
        rec = []
        for prop in bs_profiles[p]["min_props"]:
            if "|" in prop:
                shacl_alt = f'[ sh:alternativePath (  {" ".join(prop.split("|"))} ) ]'
                min.append(shacl_alt)
            else:
                min.append(prop)

        for prop in bs_profiles[p]["rec_props"]:
            if "|" in prop:
                shacl_alt = f'[ sh:alternativePath (  {" ".join(prop.split("|"))} ) ]'
                rec.append(shacl_alt)
            else:
                rec.append(prop)

        res[p]["rec_props"] = rec
        res[p]["min_props"] = min
        res[p]["ref_profile"] = bs_profiles[p]["ref_profile"]
    return res


bs_profiles = {
    "sc:SoftwareApplication": {
        "min_props": ["sc:name", "sc:description", "sc:url"],
        "rec_props": [
            "sc:additionalType",
            "sc:applicationCategory",
            "sc:applicationSubCategory",
            "sc:author",
            "sc:license",
            "sc:citation",
            "sc:featureList",
            "sc:softwareVersion",
        ],
        "ref_profile": "https://bioschemas.org/profiles/ComputationalTool/1.0-RELEASE",
    },
    "sc:Dataset": {
        "min_props": [
            "sc:name",
            "sc:description",
            "sc:identifier",
            "sc:keywords",
            "sc:license",
            "sc:url",
        ],
        "rec_props": [
            "sc:alternateName",
            "sc:creator",
            "sc:citation",
            "sc:distribution",
            "sc:includedInDataCatalog",
            "sc:isBasedOn",
            "sc:measurementTechnique",
            "sc:variableMeasured",
            "sc:version",
        ],
        "ref_profile": "https://bioschemas.org/profiles/Dataset/0.4-DRAFT",
    },
    "sc:ScholarlyArticle": {
        "min_props": ["sc:headline", "sc:identifier"],
        "rec_props": [
            "sc:about",
            "sc:alternateName",
            "sc:author",
            "sc:backstory",
            "sc:citation",
            "sc:dateCreated",
            "sc:dateModified",
            "sc:datePublished",
            "sc:isBasedOn",
            "sc:isPartOf",
            "sc:keywords",
            "sc:license",
            "sc:pageEnd",
            "sc:pageStart",
            "sc:url",
        ],
        "ref_profile": "https://bioschemas.org/profiles/ScholarlyArticle/0.2-DRAFT-2020_12_03",
    },
    "sc:MolecularEntity": {
        "min_props": ["sc:identifier", "sc:name", "dct:conformsTo", "sc:url"],
        "rec_props": [
            "sc:inChI",
            "sc:inChIKey",
            "sc:iupacName",
            "sc:molecularFormula",
            "sc:molecularWeight",
            "sc:smiles",
        ],
        "ref_profile": "https://bioschemas.org/profiles/MolecularEntity/0.5-RELEASE",
    },
    "sc:Gene": {
        "min_props": ["sc:identifier", "sc:name", "dct:conformsTo"],
        "rec_props": [
            "sc:description",
            "sc:encodesBioChemEntity",
            "sc:isPartOfBioChemEntity",
            "sc:url",
        ],
        "ref_profile": "https://bioschemas.org/profiles/Gene/1.0-RELEASE",
    },
    "bsc:Gene": {
        "min_props": ["sc:identifier", "sc:name", "dct:conformsTo"],
        "rec_props": [
            "sc:description",
            "sc:encodesBioChemEntity",
            "sc:isPartOfBioChemEntity",
            "sc:url",
        ],
        "ref_profile": "https://bioschemas.org/profiles/Gene/1.0-RELEASE",
    },
    "sc:Study": {
        "min_props": [
            "sc:identifier",
            "sc:name",
            "dct:conformsTo",
            "sc:author",
            "sc:datePublished",
            "sc:description",
            "bsc:studyDomain",
            "sc:studySubject",
        ],
        "rec_props": [
            "sc:about",
            "sc:additionnalProperty",
            "sc:citation",
            "sc:creator",
            "sc:dateCreated",
            "sc:endDate",
            "sc:keywords",
            "sc:startDate",
            "sc:studyLocation",
            "bsc:studyProcess",
            "sc:url",
        ],
        "ref_profile": "https://bioschemas.org/profiles/Study/0.2-DRAFT",
    },
    "sc:Person": {
        "min_props": [
            "sc:description",
            "sc:name",
            "dct:conformsTo",
            "sc:mainEntityOfPage",
        ],
        "rec_props": [
            "sc:email",
            "bsc:expertise",
            "sc:homeLocation",
            "sc:image",
            "sc:memberOf",
            "bsc:orcid",
            "sc:worksFor",
        ],
        "ref_profile": "https://bioschemas.org/profiles/Person/0.2-DRAFT-2019_07_19",
    },
    "sc:SoftwareSourceCode": {
        "min_props": [
            "dct:conformsTo",
            "sc:creator",
            "sc:dateCreated",
            "bsc:input|sc:input",
            "sc:license",
            "sc:name",
            "bsc:output|sc:output",
            "sc:programmingLanguage",
            "sc:sdPublisher",
            "sc:url",
            "sc:version",
        ],
        "rec_props": [
            "sc:citation",
            "sc:contributor",
            "sc:creativeWorkStatus",
            "sc:description",
            "sc:documentation",
            "sc:funding",
            "sc:hasPart",
            "sc:isBasedOn",
            "sc:keywords",
            "sc:maintainer",
            "sc:producer",
            "sc:publisher",
            "sc:runtimePlatform",
            "sc:sofwtareRequirement",
            "sc:targetProduct",
        ],
        "ref_profile": "https://bioschemas.org/profiles/ComputationalWorkflow/1.0-RELEASE",
    },
    "sc:Protein": {
        "min_props": ["dct:conformsTo", "sc:identifier", "sc:name"],
        "rec_props": [
            "bsc:associatedDisease",
            "sc:description",
            "bsc:isEncodedByBioChemEntity",
            "bsc:taxonomicRange",
            "sc:url",
        ],
        "ref_profile": "https://bioschemas.org/profiles/Protein/0.11-RELEASE",
    },
    "sc:SequenceAnnotation": {
        "min_props": ["dct:conformsTo", "bsc:sequenceLocation|sc:sequenceLocation"],
        "rec_props": [
            "bsc:creationMethod",
            "sc:description",
            "sc:image",
            "sc:name",
            "sc:sameAs",
            "bsc:sequenceOrientation",
            "bsc:sequenceValue",
            "sc:url",
        ],
        "ref_profile": "https://bioschemas.org/profiles/SequenceAnnotation/0.7-DRAFT",
    },
    "sc:SequenceRange": {
        "min_props": ["dct:conformsTo", "bsc:rangeStart", "bsc:rangeEnd"],
        "rec_props": ["bsc:endUncertainty", "bsc:startUncertainty"],
        "ref_profile": "https://bioschemas.org/profiles/SequenceRange/0.1-DRAFT",
    },
    "sc:CreativeWork": {
        "min_props": ["dct:conformsTo", "sc:description", "sc:keywords", "sc:name"],
        "rec_props": [
            "sc:about",
            "sc:abstract",
            "sc:audience",
            "sc:author",
            "sc:competencyRequired",
            "sc:educationalLevel",
            "sc:identifier",
            "sc:inLanguage",
            "sc:learningResourceType",
            "sc:license",
            "sc:mentions",
            "sc:teaches",
            "sc:timeRequired",
            "sc:url",
        ],
        "ref_profile": "https://bioschemas.org/profiles/TrainingMaterial/0.9-DRAFT-2020_12_08",
    },
}

bs_profiles = gen_shacl_alternatives(bs_profiles)


# bs_profiles = generate_profiles_from_files()


def checktype(obj):
    # This if statement makes sure input is a list that is not empty
    if obj and isinstance(obj, list):
        return all(isinstance(s, str) for s in obj)
    else:
        return False


def gen_SHACL_from_target_class(target_class):
    # print(f"Generating SHACL shape for {target_class}")

    if target_class not in bs_profiles.keys():
        raise BioschemasProfileError(class_name=target_class)

    name = target_class.rsplit(":", 1)[1]
    # targets = []
    # targets.append(target_class)
    # print(bs_profiles[target_class])
    return (
        gen_SHACL_from_profile(
            name,
            [target_class],
            bs_profiles[target_class]["min_props"],
            bs_profiles[target_class]["rec_props"],
        ),
        bs_profiles[target_class]["ref_profile"],
    )


def gen_SHACL_from_profile(shape_name, target_classes, min_props, rec_props):

    # TODO type checking for parameters
    # print(shape_name)
    # print(target_classes)
    # print(min_props)
    # print(rec_props)

    shape_template = """
        @prefix ns: <https://fair-checker.france-bioinformatique.fr#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix sc: <http://schema.org/> .
        @prefix bsc: <https://bioschemas.org/> .
        @prefix dct: <http://purl.org/dc/terms/> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix edam: <http://edamontology.org/> .
        @prefix biotools: <https://bio.tools/ontology/> .

        ns:{{shape_name}}
            a sh:NodeShape ;
            #sh:targetSubjectsOf schema:name ;
            {% for c in target_classes %}
            sh:targetClass  {{c}} ;
            {% endfor %}

            {% for min_prop in min_props %}
            sh:property [
                sh:path {{min_prop}} ;
                sh:minCount 1 ;
                sh:severity sh:Violation
            ] ;
            {% endfor %}

            {% for rec_prop in rec_props %}
            sh:property [
                sh:path {{rec_prop}} ;
                sh:minCount 1 ;
                sh:severity sh:Warning
            ] ;
            {% endfor %}
        .
    """

    # [sh: alternativePath(ex:father ex: mother  )]

    template = Template(shape_template)
    shape = template.render(
        shape_name=shape_name,
        target_classes=target_classes,
        min_props=min_props,
        rec_props=rec_props,
    )
    # print(shape)

    return shape


def validate_any_from_KG(kg):
    kg.namespace_manager.bind("sc", URIRef("http://schema.org/"))
    kg.namespace_manager.bind("bsc", URIRef("https://bioschemas.org/"))
    kg.namespace_manager.bind("dct", URIRef("http://purl.org/dc/terms/"))

    # print(len(kg))
    # print(kg.serialize(format="turtle"))

    results = {}

    # list classes
    for s, p, o in kg.triples((None, RDF.type, None)):
        # print()
        # print(f"{s.n3(kg.namespace_manager)} is a {o.n3(kg.namespace_manager)}")
        # print(bs_profiles.keys())
        # print(o.n3(kg.namespace_manager))
        if o.n3(kg.namespace_manager) in bs_profiles.keys():
            # print()
            # print(f"Trying to validate {s} as a(n) {o} resource")
            shacl_shape, ref_profile = gen_SHACL_from_target_class(
                o.n3(kg.namespace_manager)
            )

            sub_kg = ConjunctiveGraph()
            for x, y, z in kg.triples((s, None, None)):
                sub_kg.add((x, y, z))

            conforms, warnings, errors = validate_shape(
                knowledge_graph=sub_kg, shacl_shape=shacl_shape
            )
            results[str(s)] = {
                "type": str(o),
                "ref_profile": ref_profile,
                "conforms": conforms,
                "warnings": warnings,
                "errors": errors,
            }

    return results


def validate_any_from_RDF(input_url, rdf_syntax):
    kg = ConjunctiveGraph()
    kg.namespace_manager.bind("sc", URIRef("http://schema.org/"))
    kg.namespace_manager.bind("bsc", URIRef("https://bioschemas.org/"))
    kg.namespace_manager.bind("dct", URIRef("http://purl.org/dc/terms/"))
    kg.parse(location=input_url, format=rdf_syntax)

    results = {}

    # list classes
    for s, p, o in kg.triples((None, RDF.type, None)):
        # print()
        # print(f"{s.n3(kg.namespace_manager)} is a {o.n3(kg.namespace_manager)}")
        if o.n3(kg.namespace_manager) in bs_profiles.keys():
            # print()
            print(f"Trying to validate {s} as a(n) {o} resource")
            shacl_shape, ref_profile = gen_SHACL_from_target_class(
                o.n3(kg.namespace_manager)
            )

            sub_kg = ConjunctiveGraph()
            for x, y, z in kg.triples((s, None, None)):
                sub_kg.add((x, y, z))

            conforms, warnings, errors = validate_shape(
                knowledge_graph=sub_kg, shacl_shape=shacl_shape
            )
            results[str(s)] = {
                "type": str(o),
                "ref_profile": ref_profile,
                "conforms": conforms,
                "warnings": warnings,
                "errors": errors,
            }
    return results


def validate_any_from_microdata(input_url):
    web_resource = WebResource(input_url)
    kg = web_resource.get_rdf()
    kg.namespace_manager.bind("sc", URIRef("http://schema.org/"))
    kg.namespace_manager.bind("bsc", URIRef("https://bioschemas.org/"))
    kg.namespace_manager.bind("dct", URIRef("http://purl.org/dc/terms/"))

    results = {}
    # print(kg.serialize(format="turtle"))

    # list classes
    for s, p, o in kg.triples((None, RDF.type, None)):
        # print()
        # print(f"{s.n3(kg.namespace_manager)} is a {o.n3(kg.namespace_manager)}")
        # print(o.n3(kg.namespace_manager))
        # print(bs_profiles.keys())

        if o.n3(kg.namespace_manager) in bs_profiles.keys():
            # print()
            print(f"Trying to validate {s} as a(n) {o} resource")
            shacl_shape, ref_profile = gen_SHACL_from_target_class(
                o.n3(kg.namespace_manager)
            )

            sub_kg = ConjunctiveGraph()
            for x, y, z in kg.triples((s, None, None)):
                sub_kg.add((x, y, z))

            conforms, warnings, errors = validate_shape(
                knowledge_graph=sub_kg, shacl_shape=shacl_shape
            )
            results[str(s)] = {
                "type": str(o),
                "ref_profile": ref_profile,
                "conforms": conforms,
                "warnings": warnings,
                "errors": errors,
            }
        else:
            print(f"Could not find a suitable profile for {s} typed {o}")
    # print(len(kg))
    return results, kg


def validate_shape_from_RDF(input_uri, rdf_syntax, shacl_shape):
    kg = ConjunctiveGraph()
    kg.parse(location=input_uri, format=rdf_syntax)
    conforms, warnings, errors = validate_shape(
        knowledge_graph=kg, shacl_shape=shacl_shape
    )
    return conforms, warnings, errors


def validate_shape_from_microdata(input_uri, shacl_shape):
    kg = WebResource(input_uri).get_rdf()
    conforms, warnings, errors = validate_shape(
        knowledge_graph=kg, shacl_shape=shacl_shape
    )
    return conforms, warnings, errors


def validate_shape(knowledge_graph, shacl_shape):
    r = validate(
        data_graph=knowledge_graph,
        data_graph_format="turtle",
        shacl_graph=shacl_shape,
        # shacl_graph = my_shacl_constraint,
        shacl_graph_format="turtle",
        ont_graph=None,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        debug=False,
    )

    conforms, results_graph, results_text = r

    report_query = """
            SELECT ?node ?path ?path ?severity WHERE {
                ?v rdf:type sh:ValidationReport ;
                   sh:result ?r .
                ?r sh:focusNode ?node ;
                   sh:sourceShape ?s .
                { ?s sh:path ?path ;
                   sh:severity ?severity . }
                UNION { ?s sh:path/sh:alternativePath/rdf:rest*/rdf:first ?path ;
                   sh:severity ?severity . }
                FILTER (! isBlank(?path))
            }
        """

    results = results_graph.query(report_query)
    # print("VALIDATION RESULTS")
    # print(results_text)
    # print(conforms)
    # print(results_graph.serialize(format="turtle"))
    warnings = []
    errors = []
    for r in results:
        if "#Warning" in r["severity"]:
            # print(f'WARNING: Property {r["path"]} should be provided for {r["node"]}')
            warnings.append(f'{r["path"]}')
        if "#Violation" in r["severity"]:
            # print(f'ERROR: Property {r["path"]} must be provided for {r["node"]}')
            errors.append(f'{r["path"]}')

    return conforms, warnings, errors
