from azure.search.documents.indexes._generated.models import FieldMapping
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchSuggester

from mcp_foundry_knowledge import (
    SearchFieldSchema,
    SuggesterSchema,
    CorsOptionsSchema,
    SearchIndexSchema,
    FieldMappingModel,
    convert_pydantic_model_to_search_index,
    convert_to_field_mappings,
)


def test_search_field_schema_defaults():
    field = SearchFieldSchema(name="title", type="Edm.String")
    assert field.name == "title"
    assert field.key is False
    assert field.retrievable is True


def test_suggester_schema():
    suggester = SuggesterSchema(name="sg", source_fields=["title", "tags"])
    assert suggester.name == "sg"
    assert suggester.source_fields == ["title", "tags"]


def test_cors_options_schema_defaults():
    cors = CorsOptionsSchema(allowed_origins=["*"])
    assert cors.allowed_origins == ["*"]
    assert cors.max_age_in_seconds == 300


def test_search_index_schema_with_minimum_fields():
    schema = SearchIndexSchema(
        name="products",
        fields=[SearchFieldSchema(name="id", type="Edm.String", key=True)]
    )
    assert schema.name == "products"
    assert len(schema.fields) == 1
    assert schema.fields[0].key is True


def test_convert_pydantic_model_to_search_index():
    schema = SearchIndexSchema(
        name="products",
        fields=[
            SearchFieldSchema(name="id", type="Edm.String", key=True),
            SearchFieldSchema(name="title", type="Edm.String", searchable=True)
        ],
        suggesters=[
            SuggesterSchema(name="sg", source_fields=["title"])
        ]
    )

    result = convert_pydantic_model_to_search_index(schema)

    assert isinstance(result, SearchIndex)
    assert result.name == "products"
    assert len(result.fields) == 2
    assert result.fields[0].name == "id"
    assert isinstance(result.suggesters[0], SearchSuggester)
    assert result.suggesters[0].source_fields == ["title"]


def test_convert_to_field_mappings():
    input_models = [
        FieldMappingModel(source_field_name="src1", target_field_name="tgt1"),
        FieldMappingModel(source_field_name="src2", target_field_name="tgt2", mapping_function="extractTokenAtPosition(1)")
    ]
    mappings = convert_to_field_mappings(input_models)

    assert len(mappings) == 2
    assert isinstance(mappings[0], FieldMapping)
    assert mappings[0].source_field_name == "src1"
    assert mappings[1].mapping_function == "extractTokenAtPosition(1)"
