def validate_material_usage(material_usage_table):
    for row in material_usage_table.get("rows", []):
        actual_quantity = row.get("actual_quantity")
        allowed_range_min = row.get("allowed_range_min")
        allowed_range_max = row.get("allowed_range_max")

        row["quantity_within_range"] = (
            allowed_range_min <= actual_quantity <= allowed_range_max
        )
    return material_usage_table
