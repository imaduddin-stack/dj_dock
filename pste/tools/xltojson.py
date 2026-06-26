import argparse
import json
import os
import pandas as pd


def excel_sheets_to_django_json(excel_file, json_output_file, default_app_name="dokumen"):
    """Reads all sheets from a workbook and combines them into one Django fixture."""
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found.")
        return

    # Read all sheets at once into a dictionary of DataFrames
    excel_sheets = pd.read_excel(excel_file, sheet_name=None)
    django_fixture = []

    for sheet_name, df in excel_sheets.items():
        # Reconstruct the model identifier (e.g., 'myapp.product')
        # If the sheet name doesn't contain a dot, prepend the default app name
        model_identifier = (
            sheet_name if "." in sheet_name else f"{default_app_name}.{sheet_name}"
        )

        for _, row in df.iterrows():
            row_dict = row.to_dict()

            # Extract primary key
            pk = row_dict.pop("django_pk")
            if pd.isna(pk):
                pk = None
            elif isinstance(pk, float) and pk.is_integer():
                pk = int(pk)

            # Parse fields
            fields = {}
            for key, val in row_dict.items():
                if pd.isna(val):
                    fields[key] = None
                else:
                    if isinstance(val, str) and (
                        val.startswith("[") or val.startswith("{")
                    ):
                        try:
                            fields[key] = json.loads(val)
                            continue
                        except json.JSONDecodeError:
                            pass
                    fields[key] = val

            django_fixture.append(
                {"model": model_identifier, "pk": pk, "fields": fields}
            )

    with open(json_output_file, "w", encoding="utf-8") as f:
        json.dump(django_fixture, f, indent=4, ensure_ascii=False)

    print(f"Ready to seed! Re-compiled fixture at: {json_output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Excel sheets to Django JSON fixture"
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input Excel file path",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output JSON fixture file path",
    )
    parser.add_argument(
        "-a",
        "--app",
        default="dokumen",
        help="Default app name for model identifiers (default: dokumen)",
    )

    args = parser.parse_args()
    excel_sheets_to_django_json(args.input, args.output, args.app)
