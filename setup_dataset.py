import os
import shutil
import pandas as pd

RAW_DIR   = "kaggle_raw"
IMAGE_DIR = "catalog/images"
CSV_OUT   = "catalog/metadata.csv"

# Fixed category names to match the actual dataset
CATEGORY_QUOTA = {
    "Shirts":       4,
    "Jeans":        3,
    "Dresses":      4,
    "Casual Shoes": 4,
    "Jackets":      3,
    "Tshirts":      4,
    "Trousers":     3,
}

def build_catalog():
    styles_csv    = os.path.join(RAW_DIR, "styles.csv")
    images_folder = os.path.join(RAW_DIR, "images")

    print("Reading styles.csv...")
    df = pd.read_csv(styles_csv, on_bad_lines="skip")

    df["image_path"] = df["id"].apply(
        lambda i: os.path.join(images_folder, f"{i}.jpg")
    )
    df = df[df["image_path"].apply(os.path.exists)].reset_index(drop=True)
    print(f"Rows with images: {len(df)}")

    os.makedirs(IMAGE_DIR, exist_ok=True)
    selected_rows = []

    for category, quota in CATEGORY_QUOTA.items():
        subset = df[df["articleType"] == category].head(quota)
        print(f"  {category}: {len(subset)} items selected")
        for _, row in subset.iterrows():
            src      = row["image_path"]
            dst_name = f"{row['id']}.jpg"
            dst      = os.path.join(IMAGE_DIR, dst_name)
            shutil.copy2(src, dst)

            colour  = str(row.get("baseColour", "")).strip()
            season  = str(row.get("season",     "")).strip()
            usage   = str(row.get("usage",      "")).strip()
            name    = str(row.get("productDisplayName", category)).strip()

            description = (
                f"{colour} {category.lower()} "
                f"{'for ' + season.lower() + ' ' if season and season != 'nan' else ''}"
                f"{'— ' + usage.lower() if usage and usage != 'nan' else ''}. "
                f"{name}."
            ).strip()

            selected_rows.append({
                "id":          int(row["id"]),
                "name":        name,
                "category":    category,
                "description": description,
                "image_file":  dst_name,
            })

    catalog_df = pd.DataFrame(selected_rows).reset_index(drop=True)
    catalog_df.to_csv(CSV_OUT, index=False)
    print(f"\nDone! {len(catalog_df)} items saved to {CSV_OUT}")
    print(catalog_df[["name", "category"]].to_string(index=False))

if __name__ == "__main__":
    build_catalog()