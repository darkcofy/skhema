"""Tests for the Excalidraw library generator."""
import json
import os
import pytest
from skhema.generate_excalidraw_lib import (
    build_library_item,
    build_library,
    C4_SHAPE_MAP_LIGHT,
)


class TestBuildLibraryItem:
    def test_container_shape(self):
        item = build_library_item(
            element_id="data_lake",
            name="Data Lake",
            description="Raw + curated zones",
            c4_type="ContainerDb",
            domain="storage",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        assert item["id"] == "data_lake"
        assert item["name"] == "Data Lake (storage)"
        assert item["status"] == "published"
        assert len(item["elements"]) == 2  # shape + text

    def test_shape_properties(self):
        item = build_library_item(
            element_id="auth_gateway",
            name="Auth Gateway",
            description="API auth enforcement",
            c4_type="Container",
            domain="security",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        shape = item["elements"][0]
        assert shape["type"] == "rectangle"
        assert shape["roughness"] == 2
        assert shape["backgroundColor"] == "#FEF3C7"
        assert shape["strokeColor"] == "#D97706"
        assert shape["strokeStyle"] == "solid"
        assert shape["roundness"] == {"type": 3}

    def test_external_dashed(self):
        item = build_library_item(
            element_id="firewall",
            name="Firewall",
            description="Network perimeter",
            c4_type="Container_Ext",
            domain="security",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        shape = item["elements"][0]
        assert shape["strokeStyle"] == "dashed"
        assert shape["backgroundColor"] == "#F5F5F4"

    def test_person_emoji_prefix(self):
        item = build_library_item(
            element_id="data_analyst",
            name="Data Analyst",
            description="Queries data",
            c4_type="Person",
            domain="consumers",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        text = item["elements"][1]
        assert text["text"].startswith("👤")

    def test_db_emoji_prefix(self):
        item = build_library_item(
            element_id="data_lake",
            name="Data Lake",
            description="Raw zones",
            c4_type="ContainerDb",
            domain="storage",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        text = item["elements"][1]
        assert text["text"].startswith("🗄")

    def test_group_ids_shared(self):
        item = build_library_item(
            element_id="test_elem",
            name="Test",
            description="Desc",
            c4_type="Container",
            domain="test",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        shape = item["elements"][0]
        text = item["elements"][1]
        assert shape["groupIds"] == text["groupIds"]
        assert len(shape["groupIds"]) == 1

    def test_text_bound_to_shape(self):
        item = build_library_item(
            element_id="test_elem",
            name="Test",
            description="Desc",
            c4_type="Container",
            domain="test",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        shape = item["elements"][0]
        text = item["elements"][1]
        assert text["containerId"] == shape["id"]
        assert {"id": text["id"], "type": "text"} in shape["boundElements"]

    def test_deterministic_seed(self):
        item1 = build_library_item("x", "X", "d", "Container", "t", C4_SHAPE_MAP_LIGHT)
        item2 = build_library_item("x", "X", "d", "Container", "t", C4_SHAPE_MAP_LIGHT)
        assert item1["elements"][0]["seed"] == item2["elements"][0]["seed"]


class TestBuildLibrary:
    def test_structure(self):
        manifest = {
            "storage": [
                {"id": "data_lake", "type": "ContainerDb", "description": "Raw zones"},
            ]
        }
        lib = build_library(manifest, C4_SHAPE_MAP_LIGHT)
        assert lib["type"] == "excalidrawlib"
        assert lib["version"] == 2
        assert len(lib["libraryItems"]) == 1

    def test_valid_json(self):
        manifest = {
            "storage": [
                {"id": "data_lake", "type": "ContainerDb", "description": "Raw zones"},
            ]
        }
        lib = build_library(manifest, C4_SHAPE_MAP_LIGHT)
        # Should be serializable
        output = json.dumps(lib, indent=2)
        parsed = json.loads(output)
        assert parsed["type"] == "excalidrawlib"
