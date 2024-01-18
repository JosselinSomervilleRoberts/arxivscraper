import arxivscraper
from urllib.request import urlretrieve
import tarfile
import os
from typing import List, Optional, Tuple, Dict
from tqdm import tqdm
import shutil
import json
from PIL import Image
import time

from constants import TEX_DELIMITERS, TEX_BEGIN, TEX_END
from renderer import latex_to_image
import os
import re
import random
import numpy as np
import signal
from datetime import datetime, timedelta


# Define the function to handle the timeout
def handler(signum, frame):
    raise Exception("Download timed out")


# Function to download the file with exception handling and timeout
def download_file(download_url, filename, timeout_seconds=30):
    try:
        # Set the timeout signal
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_seconds)

        # Attempt to download the file
        urlretrieve(download_url, filename)
        signal.alarm(0)  # Reset the alarm
        return True
    except Exception as e:
        return False


def gather_papers(
    category: str,
    date_from: str,
    date_until: str,
    data_path: str = "data",
    num_papers: int = 100,
    carry: int = 0,
    infos: Optional[dict] = None,
) -> Tuple[List[str], dict]:
    """Gather papers from arXiv.org.

    Args:
        category (str, optional): Category of the papers.
        date_from (str, optional): Starting date.
        date_until (str, optional): Ending date.

    Returns:
        papers (List[str]): List of papers tex codes.
    """
    TMP_FILE = "tmp.tar.gz"
    TMP_DIR = "tmp_dir"

    """Test main function. The output should 97 entries."""
    scraper = arxivscraper.Scraper(
        category=category,
        date_from=date_from,
        date_until=date_until,
    )

    os.makedirs(f"{data_path}/assets", exist_ok=True)

    outputs = scraper.scrape()

    papers: List[str] = []
    num_scrapped, num_downloaded, num_extracted, num_read = 0, 0, 0, 0

    if isinstance(outputs, list):
        # Shuffle outputs
        random.shuffle(outputs)
        num_scrapped = len(outputs)

        with tqdm(
            total=min(num_papers, len(outputs)), desc="Downloading papers"
        ) as pbar:
            for output in outputs:
                url = output["url"]
                doi = url.split("/")[-1]
                download_url = "https://arxiv.org/e-print/" + doi

                # Download the .tar.gz file
                successful = download_file(download_url, filename=TMP_FILE)
                if successful:
                    num_downloaded += 1

                    # Extract the .tar.gz file in a temporary directory
                    # Creates the dir (ok if it already exists)
                    os.makedirs(TMP_DIR, exist_ok=True)
                    try:
                        with tarfile.open(TMP_FILE, "r:gz") as tar:
                            # Extract all the contents into the current directory
                            tar.extractall(path=TMP_DIR)
                        num_extracted += 1
                        asset_mapping = {}

                        # Search for all '.tex' file in the extracted directory
                        has_tex_file = False
                        for root, dirs, files in os.walk(TMP_DIR):
                            for file in files:
                                if file.endswith(".tex"):
                                    try:
                                        with open(os.path.join(root, file), "r") as f:
                                            try:
                                                tex_code = f.read()
                                                asset_names = get_asset_names_used(
                                                    tex_code
                                                )

                                                # Rename the assets by replacing / by _ and adding num_extracted _ at the beginning
                                                for original_name in asset_names:
                                                    original_name_with_extension = (
                                                        original_name
                                                    )
                                                    if (
                                                        not "."
                                                        in original_name_with_extension
                                                    ):
                                                        # Find a file starting with the original_name to determine the extension
                                                        file_name = original_name_with_extension.split(
                                                            "/"
                                                        )[
                                                            -1
                                                        ]
                                                        for (
                                                            root,
                                                            dirs,
                                                            files,
                                                        ) in os.walk(
                                                            os.path.join(
                                                                TMP_DIR,
                                                                "/".join(
                                                                    original_name_with_extension.split(
                                                                        "/"
                                                                    )[
                                                                        :-1
                                                                    ]
                                                                ),
                                                            )
                                                        ):
                                                            for file in files:
                                                                if file.startswith(
                                                                    file_name
                                                                ):
                                                                    extension = os.path.splitext(
                                                                        file
                                                                    )[
                                                                        1
                                                                    ]
                                                                    original_name_with_extension += (
                                                                        extension
                                                                    )
                                                                    break
                                                    new_name = (
                                                        str(num_extracted + carry)
                                                        + "_"
                                                        + original_name_with_extension.replace(
                                                            "/", "_"
                                                        )
                                                    )
                                                    asset_mapping[new_name] = [
                                                        original_name,
                                                        original_name_with_extension,
                                                    ]

                                                for new_name, [
                                                    original_name,
                                                    original_name_with_extension,
                                                ] in asset_mapping.items():
                                                    tex_code = tex_code.replace(
                                                        original_name, new_name
                                                    )

                                                papers.append(tex_code)
                                                has_tex_file = True
                                            except UnicodeDecodeError:
                                                pass
                                    except FileNotFoundError:
                                        pass

                        # Copy the assets
                        for new_name, [
                            original_name,
                            original_name_with_extension,
                        ] in asset_mapping.items():
                            asset_path = os.path.join(
                                TMP_DIR, original_name_with_extension
                            )
                            new_asset_path = os.path.join(
                                f"{data_path}/assets", new_name
                            )
                            try:
                                shutil.copy(asset_path, new_asset_path)
                            except FileNotFoundError:
                                pass

                        # Remove the temporary directory (and its contents)
                        shutil.rmtree(TMP_DIR)

                        # Update progress bar and break once we have enough papers
                        if has_tex_file:
                            num_read += 1
                            pbar.update(1)
                            if num_read >= num_papers:
                                break
                    except tarfile.ReadError:
                        pass

                    # Remove the .tar.gz file
                    os.remove(TMP_FILE)

    if infos is None:
        infos = {}
    infos["num_scrapped"] = num_scrapped + infos.get("num_scrapped", 0)
    infos["num_downloaded"] = num_downloaded + infos.get("num_downloaded", 0)
    infos["num_extracted"] = num_extracted + infos.get("num_extracted", 0)
    infos["num_read"] = num_read + infos.get("num_read", 0)
    infos["num_files"] = len(papers) + infos.get("num_files", 0)
    return papers, infos


def get_asset_names_used(latex_code: str) -> List[str]:
    content, _ = get_delimited_content([latex_code], {}, categories=["figure"])
    list_figures = content["figure"]
    pattern = r"\\includegraphics(?:\[[^\]]+\])?\{([^}]+)\}"

    asset_names = []
    for figure in list_figures:
        matches = re.findall(pattern, figure)
        asset_names.extend(matches)

    return asset_names


def get_delimited_content(
    list_src_code: List[str], infos: dict, categories: Optional[List[str]] = None
) -> Tuple[Dict[str, List[str]], dict]:
    """Given a tex source code, return a dictionarry mapping categories (equation, plot, table, ...) to
    all the instances of that category in the source codes.

    Args:
        list_src_code (List[str]): List of tex source codes.
        infos (dict): informations on the scrapping process.

    Returns:
        Dict[str, List[str]]: Dictionnary mapping a category to the list of delimited instances
        infos (dict): informations added.
    """
    delimited_content: Dict[str, List[str]] = {}

    for category, (must_contain, delimiters) in TEX_DELIMITERS.items():
        # Skip the category if it is not in the list of categories
        if categories is not None and category not in categories:
            continue

        delimited_content[category] = []
        for delimiter in delimiters:
            start, end = delimiter
            for src_code in list_src_code:
                lines = src_code.split("\n")  # Split the source code into lines
                start_idx, end_idx = None, None
                content = ""

                for line in lines:
                    stripped_line = line.strip()

                    # Skip commented lines
                    if stripped_line.startswith("%"):
                        continue

                    # Check for the start delimiter
                    if start_idx is None:
                        if start in stripped_line:
                            start_idx = lines.index(line)
                            content += line + "\n"
                            continue

                    # If we are in an environment, add the line to content
                    if start_idx is not None:
                        content += line + "\n"

                    # Check for the end delimiter
                    if end in stripped_line:
                        end_idx = lines.index(line)
                        if start_idx is not None and end_idx is not None:
                            # We only add the content to the category if it contains the must_contain string
                            if must_contain is None or must_contain in content:
                                delimited_content[category].append(content)
                            start_idx, end_idx = None, None
                            content = ""

        # Remove duplicates
        original_num = len(delimited_content[category])
        delimited_content[category] = list(set(delimited_content[category]))

        if category not in infos:
            infos[category] = {}
        infos[category]["number_of_original_samples"] = original_num + infos[
            category
        ].get("number_of_original_samples", 0)
        infos[category]["number_of_unique_samples"] = len(
            delimited_content[category]
        ) + infos[category].get("number_of_unique_samples", 0)
    return delimited_content, infos


def get_and_save_rendering_from_delimited_content(
    delimited_content: Dict[str, List[str]],
    infos: dict,
    data_path: str = "data",
    num_per_category: Optional[Dict[str, int]] = None,
):
    """Given a dictionnary of delimited content, render all the images.
    Save them directly.

    Args:
        delimited_content (Dict[str, List[str]]): Dictionnary mapping a category to the list of delimited instances
        infos (dict): informations on the scrapping process.
    """

    for category, list_of_content in delimited_content.items():
        num_instances = len(list_of_content)
        os.makedirs(f"{data_path}/images/{category}s", exist_ok=True)
        os.makedirs(f"{data_path}/contents_filtered/{category}s", exist_ok=True)
        os.makedirs(f"{data_path}/assets_used", exist_ok=True)
        num_images = (
            0
            if "number_of_images" not in infos[category]
            else infos[category]["number_of_images"]
        )

        num_max_image = (
            num_per_category[category]
            if num_per_category is not None
            else num_images + num_instances + 1
        )

        with tqdm(total=num_instances, desc=f"Rendering {category}") as pbar:
            for tex_code in list_of_content:
                try:
                    image, dimensions = latex_to_image(
                        TEX_BEGIN + tex_code + TEX_END,
                        assets_path=f"{data_path}/assets",
                        crop=True,
                    )
                    # Check if the image is not fully white
                    if image is not None and not np.allclose(image, 255):
                        # Save the image
                        image.save(
                            f"{data_path}/images/{category}s/{category}_{num_images}.png"
                        )
                        # Save the associated code
                        with open(
                            f"{data_path}/contents_filtered/{category}s/{category}_{num_images}.tex",
                            "w",
                        ) as f:
                            f.write(tex_code)
                        # Save the associated assets
                        asset_names = get_asset_names_used(tex_code)
                        for asset_name in asset_names:
                            asset_path = os.path.join(f"{data_path}/assets", asset_name)
                            new_asset_path = os.path.join(
                                f"{data_path}/assets_used",
                                asset_name.replace("/", "_"),
                            )
                            try:
                                shutil.copy(asset_path, new_asset_path)
                            except FileNotFoundError:
                                pass
                        num_images += 1
                        if num_images >= num_max_image:
                            break

                except Exception as e:
                    pass
                pbar.update(1)

        if category not in infos:
            infos[category] = {}
        infos[category]["number_of_images"] = num_images + infos[category].get(
            "number_of_images", 0
        )
        infos[category]["number_of_images_not_rendered"] = (
            num_instances
            - num_images
            + infos[category].get("number_of_images_not_rendered", 0)
        )

    save_infos(infos, data_path=data_path)


def save_infos(infos: dict, data_path: str = "data"):
    """Save the information about the scrapped papers.

    Args:
        infos (dict): Information about the scrapped papers.
    """
    os.makedirs(data_path, exist_ok=True)
    with open(f"{data_path}/infos.json", "w") as f:
        json.dump(infos, f, indent=4)


def read_infos(data_path: str = "data") -> dict:
    """Read the information about the scrapped papers.

    Returns:
        dict: Information about the scrapped papers.
    """
    with open(f"{data_path}/infos.json", "r") as f:
        infos = json.load(f)
    return infos


def save_scrapped_papers(
    papers: List[str],
    infos: Optional[dict] = None,
    data_path: str = "data",
    carry: int = 0,
):
    """Save the scrapped papers.

    Args:
        papers (List[str]): List of papers tex codes.
        infos (dict): Information about the scrapped papers.
    """
    os.makedirs(f"{data_path}/papers", exist_ok=True)
    for i, paper in enumerate(papers):
        with open(f"{data_path}/papers/paper_{i + carry}.tex", "w") as f:
            f.write(paper)

    if infos is not None:
        save_infos(infos, data_path=data_path)


def read_scrapped_papers(data_path: str = "data") -> Tuple[List[str], dict]:
    """Read the scrapped papers.

    Returns:
        List[str]: List of papers tex codes.
        dict: Information about the scrapped papers.
    """
    papers: List[str] = []
    for root, dirs, files in os.walk(f"{data_path}/papers"):
        for file in files:
            if file.endswith(".tex"):
                with open(os.path.join(root, file), "r") as f:
                    try:
                        tex_code = f.read()
                        papers.append(tex_code)
                    except UnicodeDecodeError:
                        pass

    infos = read_infos(data_path=data_path)
    return papers, infos


def save_delimited_content(
    delimited_content: Dict[str, List[str]],
    infos: Optional[dict] = None,
    data_path: str = "data",
):
    """Save the equations.

    Args:
        delimited_content (Dict[str, List[str]]): Dictionnary mapping a category to the list of delimited instances
    """
    os.makedirs(f"{data_path}/contents", exist_ok=True)

    for category, content in delimited_content.items():
        os.makedirs(f"{data_path}/contents/{category}s", exist_ok=True)
        for i, tex_code in enumerate(content):
            with open(f"{data_path}/contents/{category}s/{category}_{i}.tex", "w") as f:
                f.write(tex_code)
    if infos is not None:
        save_infos(infos, data_path=data_path)


def read_delimited_content(
    data_path: str = "data",
) -> Tuple[Dict[str, List[str]], dict]:
    """Read the equations.

    Returns:
        Dict[str, List[str]]: Dictionnary mapping a category to the list of delimited instances
        dict: Information about the scrapped papers.
    """
    delimited_content: Dict[str, List[str]] = {}

    data_folder = f"{data_path}/contents"
    excluded_folders = ["papers", "images"]

    for root, dirs, _ in os.walk(data_folder):
        dirs[:] = [d for d in dirs if d not in excluded_folders]
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            category = folder_path.split("/")[-1][:-1]
            print(f"Reading category {category} from path: {folder_path}")
            delimited_content[category] = []

            for _, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(".tex"):
                        with open(os.path.join(folder_path, file), "r") as f:
                            try:
                                tex_code = f.read()
                                delimited_content[category].append(tex_code)
                            except UnicodeDecodeError:
                                pass

    infos = read_infos(data_path=data_path)
    return delimited_content, infos


def get_day_before(date_str: str) -> str:
    # Convert string to datetime object
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Subtract one day
    day_before = date_obj - timedelta(days=2)

    # Convert back to string
    day_before_str = day_before.strftime("%Y-%m-%d")
    return day_before_str


def end_to_end(
    paper_categories: List[str],
    date_until: str,
    num_instances_per_tex_category: Dict[str, int],
):
    for category in paper_categories:
        print(f"\n\n=============== Starting {category} ===============")
        data_path = f"data/{category}"
        infos = {}

        collected_tex_instances = {
            key: 0 for key in num_instances_per_tex_category.keys()
        }

        while True:
            tex_categories = []
            looking_for = {}  # For display
            for tex_category, num_instances in num_instances_per_tex_category.items():
                if collected_tex_instances[tex_category] < num_instances:
                    tex_categories.append(tex_category)
                looking_for[tex_category] = (
                    num_instances - collected_tex_instances[tex_category]
                )

            print(
                f"Scrapping papers in {category} between {get_day_before(date_until)} and {date_until}..."
            )
            print(f"Looking for: {looking_for} instances")
            papers, infos = gather_papers(
                category=category,
                date_from=get_day_before(date_until),
                date_until=date_until,
                data_path=data_path,
                num_papers=200,
                carry=infos.get("num_extracted", 0),
                infos=infos,
            )
            date_until = get_day_before(date_until)
            save_scrapped_papers(
                papers, infos, data_path=data_path, carry=infos.get("num_extracted", 0)
            )

            # Delimit the content
            delimited_content, infos = get_delimited_content(
                papers, infos, categories=tex_categories
            )

            # Shuffle the content
            for category in delimited_content:
                random.shuffle(delimited_content[category])

            # Get the rendering
            get_and_save_rendering_from_delimited_content(
                delimited_content,
                infos,
                data_path=data_path,
                num_per_category=num_instances_per_tex_category,
            )
            for key in collected_tex_instances.keys():
                if key in infos:
                    collected_tex_instances[key] = infos[key].get("number_of_images", 0)
            print("\n\n")
            time.sleep(5)  # To avoid 503


if __name__ == "__main__":
    categories = ["econ", "eess", "math", "physics", "q-bio", "q-fin", "stat", "cs"]
    date_until: str = "2024-01-14"
    num_instances_per_tex_category = {
        "equation": 10,
        "figure": 10,
        "table": 10,
        "algorithm": 10,
        "plot": 10,
    }
    end_to_end(categories, date_until, num_instances_per_tex_category)

# if __name__ == "__main__":
#     categories = ["econ", "eess", "math", "physics", "q-bio", "q-fin", "stat", "cs"]
#     date_from: str = "2024-01-01"
#     date_until: str = "2024-01-02"
#     num_papers_per_category = 200

#     for category in categories:
#         print(f"\n\n===== Starting {category} =====")
#         data_path = f"data/{category}"

#         # Check if data/papers exists
#         if os.path.exists(f"{data_path}/images"):
#             print("Images already exist.")
#         else:
#             if os.path.exists(f"{data_path}/contents"):
#                 print("Delimited content already exist.")
#                 delimited_content, infos = read_delimited_content(data_path=data_path)
#             else:
#                 if os.path.exists(f"{data_path}/papers"):
#                     print("Papers already exist.")
#                     papers, infos = read_scrapped_papers(data_path=data_path)
#                 else:
#                     print("Scrapping papers...")
#                     papers, infos = gather_papers(
#                         category=category,
#                         date_from=date_from,
#                         date_until=date_until,
#                         data_path=data_path,
#                         num_papers=num_papers_per_category,
#                     )
#                     save_scrapped_papers(papers, infos, data_path=data_path)
#                 delimited_content, infos = get_delimited_content(papers, infos)
#                 save_delimited_content(delimited_content, infos, data_path=data_path)
#             get_and_save_rendering_from_delimited_content(
#                 delimited_content, infos, data_path=data_path
#             )
