import json
import os
import argparse
import pandas as pd


def json_to_excel_sheets(json_file, excel_file):
    """Converts a Django dumpdata JSON file into a multi-sheet Excel workbook.

    Each distinct Django model gets its own tab.
    """
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found.")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("The JSON file is empty.")
        return

    # Dictionary to hold records grouped by model name
    # e.g., {'auth.user': [...], 'myapp.product': [...]}
    grouped_data = {}

    for item in data:
        model_name = item.get("model")
        if not model_name:
            continue

        # Setup base row structure
        row = {"django_pk": item.get("pk")}

        # Unpack fields
        fields = item.get("fields", {})
        for key, value in fields.items():
            if isinstance(value, (list, dict)):
                row[key] = json.dumps(value)
            else:
                row[key] = value

        if model_name not in grouped_data:
            grouped_data[model_name] = []

        grouped_data[model_name].append(row)

    # Write each group to its own Excel sheet
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        for model_name, records in grouped_data.items():
            df = pd.DataFrame(records)

            # Reorder columns to put primary key first
            cols = ["django_pk"] + [c for c in df.columns if c != "django_pk"]
            df = df[cols]

            # Excel sheet names have a 31-character limit.
            # Chop off the app name prefix if it makes the name too long.
            sheet_name = model_name
            if len(sheet_name) > 31:
                sheet_name = sheet_name.split(".")[-1][:31]

            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Added sheet: {sheet_name} ({len(records)} rows)")

    print(f"\nSuccess! Multi-sheet template generated at: {excel_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Django dumpdata JSON to multi-sheet Excel")
    parser.add_argument("-i", "--input", required=True, help="Input JSON file path")
    parser.add_argument("-o", "--output", required=True, help="Output Excel file path")

    args = parser.parse_args()
    json_to_excel_sheets(args.input, args.output)
