import csv
import os
from main import get_asset_names_used

SUBJECTS = ["cs", "q-bio", "q-fin", "stat"]
COLUMNS = [
    "id",
    "tex_code",
    "category",
    "subject",
    "asset_1",
    "asset_2",
    "asset_3",
    "asset_4",
    "asset_5",
    "asset_6",
    "output",
]


def create_csv_file():
    with open("dataset.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(COLUMNS)
        id_counter = 1
        for subject in SUBJECTS:
            for category in os.listdir(f"data/{subject}/contents"):
                category = category[:-1]  # Removing s
                print(f"Category {category}")
                for i in range(
                    0, len(os.listdir(f"data/{subject}/contents/{category}s"))
                ):
                    tex_code_path = (
                        f"data/{subject}/contents/{category}s/{category}_{i}.tex"
                    )
                    image_path = f"data/{subject}/images/{category}s/{category}_{i}.png"
                    if os.path.exists(tex_code_path) and os.path.exists(image_path):
                        tex_code = open(tex_code_path).read()
                        assets = get_asset_names_used(tex_code)
                        for i in range(len(assets)):
                            assets[i] = f"assets/{subject}/{assets[i]}"
                        if len(assets) <= 6:
                            row = (
                                [id_counter, tex_code_path, category, subject]
                                + assets
                                + ["" for i in range(6 - len(assets))]
                                + [image_path]
                            )
                            writer.writerow(row)
                            id_counter += 1
                        else:
                            print(
                                f"Skipping entry {id_counter} due to more than 6 assets."
                            )
                    else:
                        print(
                            f"Skipping entry {id_counter} due to missing tex_code or image."
                        )
                    id_counter += 1


create_csv_file()
