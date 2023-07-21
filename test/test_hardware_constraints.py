import pytest
from qarnot.hardware_constraint import (HardwareConstraint, MinimumRamHardware, MaximumRamHardware, MinimumCoreHardware,
    MaximumCoreHardware, MinimumRamCoreRatioHardware, MaximumRamCoreRatioHardware, GpuHardware, NoGpuHardware,
    NoSSDHardware, SSDHardware, SpecificHardware, CpuModelHardware)

class TestHardwareConstraintsDeserialization:
    def test_valid_MinimumRamHardware_deserialization(self):
        json = {
            "discriminator": "MinimumRamHardwareConstraint",
            "minimumMemoryMB": 32000.0
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to MinimumRamHardware using discriminator"
        assert isinstance(constraint, MinimumRamHardware), "Constraint should deserialize to MinimumRamHardware using discriminator"
        assert constraint._minimum_memory_mb == 32000.0, "MinimumRamHardware's minimum memory MB value should be set from json"
        json_dict = constraint.to_json()
        assert "MinimumRamHardwareConstraint" == json_dict["discriminator"], "MinimumRamHardware should serialize with correct discriminator"
        assert 32000 == json_dict["minimumMemoryMB"], "MinimumRamHardware's minimum memory MB value should be serialized in json"

    def test_valid_MaximumRamHardware_deserialization(self):
        json = {
            "discriminator": "MaximumRamHardwareConstraint",
            "maximumMemoryMB": 32000.0
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to MaximumRamHardware using discriminator"
        assert isinstance(constraint, MaximumRamHardware), "Constraint should deserialize to MaximumRamHardware using discriminator"
        assert constraint._maximum_memory_mb == 32000.0, "MaximumRamHardware's maximum memory MB value should be set from json"
        json_dict = constraint.to_json()
        assert "MaximumRamHardwareConstraint" == json_dict["discriminator"], "MaximumRamHardware should serialize with correct discriminator"
        assert 32000 == json_dict["maximumMemoryMB"], "MaximumRamHardware's maximum memory MB value should be serialized in json"

    def test_valid_MinimumCoreHardware_deserialization(self):
        json = {
            "discriminator": "MinimumCoreHardwareConstraint",
            "coreCount": 8
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to MinimumCoreHardware using discriminator"
        assert isinstance(constraint, MinimumCoreHardware), "Constraint should deserialize to MinimumCoreHardware using discriminator"
        assert constraint._core_count == 8, "MinimumCoreHardware's minimum core count value should be set from json"
        json_dict = constraint.to_json()
        assert "MinimumCoreHardwareConstraint" == json_dict["discriminator"], "MinimumCoreHardware should serialize with correct discriminator"
        assert 8 == json_dict["coreCount"], "MinimumCoreHardware's minimum core count value should be serialized in json"

    def test_valid_MaximumCoreHardware_deserialization(self):
        json = {
            "discriminator": "MaximumCoreHardwareConstraint",
            "coreCount": 16
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to MaximumCoreHardware using discriminator"
        assert isinstance(constraint, MaximumCoreHardware), "Constraint should deserialize to MaximumCoreHardware using discriminator"
        assert constraint._core_count == 16, "MaximumCoreHardware's maximum core count value should be set from json"
        json_dict = constraint.to_json()
        assert "MaximumCoreHardwareConstraint" == json_dict["discriminator"], "MaximumCoreHardware should serialize with correct discriminator"
        assert 16 == json_dict["coreCount"], "MaximumCoreHardware's maximum core count value should be serialized in json"

    def test_valid_MinimumRamCoreRatioHardware_deserialization(self):
        json = {
            "discriminator": "MinimumRamCoreRatioHardwareConstraint",
            "minimumMemoryGBCoreRatio": 2.0
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to MinimumRamCoreRatioHardware using discriminator"
        assert isinstance(constraint, MinimumRamCoreRatioHardware), "Constraint should deserialize to MinimumRamCoreRatioHardware using discriminator"
        assert constraint._minimum_memory_gb_core_ratio == 2.0, "MinimumRamCoreRatioHardware's minimum ram/core ratio value should be set from json"
        json_dict = constraint.to_json()
        assert "MinimumRamCoreRatioHardwareConstraint" == json_dict["discriminator"], "MinimumRamCoreRatioHardware should serialize with correct discriminator"
        assert 2 == json_dict["minimumMemoryGBCoreRatio"], "MinimumRamCoreRatioHardware's minimum ram/core ratio value should be serialized in json"

    def test_valid_MaximumRamCoreRatioHardware_deserialization(self):
        json = {
            "discriminator": "MaximumRamCoreRatioHardwareConstraint",
            "maximumMemoryGBCoreRatio": 4.0
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to MaximumRamCoreRatioHardware using discriminator"
        assert isinstance(constraint, MaximumRamCoreRatioHardware), "Constraint should deserialize to MaximumRamCoreRatioHardware using discriminator"
        assert constraint._maximum_memory_gb_core_ratio == 4.0, "MaximumRamCoreRatioHardware's maximum ram/core ratio value should be set from json"
        json_dict = constraint.to_json()
        assert "MaximumRamCoreRatioHardwareConstraint" == json_dict["discriminator"], "MaximumRamCoreRatioHardware should serialize with correct discriminator"
        assert 4 == json_dict["maximumMemoryGBCoreRatio"], "MaximumRamCoreRatioHardware's maximum ram/core ratio value should be serialized in json"

    def test_valid_GpuHardware_deserialization(self):
        json = {
            "discriminator": "GpuHardwareConstraint"
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to GpuHardware using discriminator"
        assert isinstance(constraint, GpuHardware), "Constraint should deserialize to GpuHardware using discriminator"
        json_dict = constraint.to_json()
        assert "GpuHardwareConstraint" == json_dict["discriminator"], "GpuHardware should serialize with correct discriminator"

    def test_valid_NoGpuHardware_deserialization(self):
        json = {
            "discriminator": "NoGpuHardwareConstraint"
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to NoGpuHardware using discriminator"
        assert isinstance(constraint, NoGpuHardware), "Constraint should deserialize to NoGpuHardware using discriminator"
        json_dict = constraint.to_json()
        assert "NoGpuHardwareConstraint" == json_dict["discriminator"], "NoGpuHardware should serialize with correct discriminator"

    def test_valid_NoSSDHardware_deserialization(self):
        json = {
            "discriminator": "NoSSDHardwareConstraint"
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to NoSSDHardware using discriminator"
        assert isinstance(constraint, NoSSDHardware), "Constraint should deserialize to NoSSDHardware using discriminator"
        json_dict = constraint.to_json()
        assert "NoSSDHardwareConstraint" == json_dict["discriminator"], "NoSSDHardware should serialize with correct discriminator"

    def test_valid_SSDHardware_deserialization(self):
        json = {
            "discriminator": "SSDHardwareConstraint"
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to SSDHardware using discriminator"
        assert isinstance(constraint, SSDHardware), "Constraint should deserialize to SSDHardware using discriminator"
        json_dict = constraint.to_json()
        assert "SSDHardwareConstraint" == json_dict["discriminator"], "SSDHardware should serialize with correct discriminator"

    def test_valid_SpecificHardware_deserialization(self):
        json = {
            "discriminator": "SpecificHardwareConstraint",
            "specificationKey": "4c-16g-intel-i73770k"
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to SpecificHardware using discriminator"
        assert isinstance(constraint, SpecificHardware), "Constraint should deserialize to SpecificHardware using discriminator"
        assert constraint._specification_key == "4c-16g-intel-i73770k", "SpecificHardware's specification key value should be set from json"
        json_dict = constraint.to_json()
        assert "SpecificHardwareConstraint" == json_dict["discriminator"], "SpecificHardware should serialize with correct discriminator"
        assert "4c-16g-intel-i73770k" == json_dict["specificationKey"], "SpecificHardware's specification key value should be serialized in json"

    def test_valid_CpuModelHardware_deserialization(self):
        json = {
            "discriminator": "CpuModelHardwareConstraint",
            "cpuModel": "i7-3770K"
        }
        constraint = HardwareConstraint.from_json(json)
        assert constraint is not None, "Constraint should deserialize to CpuModelHardware using discriminator"
        assert isinstance(constraint, CpuModelHardware), "Constraint should deserialize to CpuModelHardware using discriminator"
        assert constraint._cpu_model == "i7-3770K", "CpuModelHardware's cpu model value should be set from json"
        json_dict = constraint.to_json()
        assert "CpuModelHardwareConstraint" == json_dict["discriminator"], "CpuModelHardware should serialize with correct discriminator"
        assert "i7-3770K" == json_dict["cpuModel"], "CpuModelHardware's cpu model value should be serialized in json"
