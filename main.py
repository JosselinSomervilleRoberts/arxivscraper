import arxivscraper
from urllib.request import urlretrieve
import tarfile
import os
from typing import List, Optional, Tuple, Dict
from tqdm import tqdm
import shutil
import json
from PIL import Image

from constants import TEX_DELIMITERS, TEX_BEGIN, TEX_END
from renderer import latex_to_image
import os
import re


def gather_papers(
    category: str = "physics:cond-mat",
    date_from: str = "2017-05-27",
    date_until: str = "2017-05-29",
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

    os.makedirs("data", exist_ok=True)
    os.makedirs("data/assets", exist_ok=True)

    outputs = scraper.scrape()
    papers: List[str] = []
    num_scrapped, num_downloaded, num_extracted, num_read = len(outputs), 0, 0, 0

    for output in tqdm(outputs, desc="Downloading papers"):
        url = output["url"]
        doi = url.split("/")[-1]
        download_url = "https://arxiv.org/e-print/" + doi

        # Download the .tar.gz file
        urlretrieve(download_url, filename=TMP_FILE)
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
                        with open(os.path.join(root, file), "r") as f:
                            try:
                                tex_code = f.read()
                                asset_names = get_asset_names_used(tex_code)

                                # Rename the assets by replacing / by _ and adding num_extracted _ at the beginning
                                for original_name in asset_names:
                                    original_name_with_extension = original_name
                                    if not "." in original_name_with_extension:
                                        # Find a file starting with the original_name to determine the extension
                                        file_name = original_name_with_extension.split(
                                            "/"
                                        )[-1]
                                        for root, dirs, files in os.walk(
                                            os.path.join(
                                                TMP_DIR,
                                                "/".join(
                                                    original_name_with_extension.split(
                                                        "/"
                                                    )[:-1]
                                                ),
                                            )
                                        ):
                                            for file in files:
                                                if file.startswith(file_name):
                                                    extension = os.path.splitext(file)[
                                                        1
                                                    ]
                                                    original_name_with_extension += (
                                                        extension
                                                    )
                                                    break
                                    new_name = (
                                        str(num_extracted)
                                        + "_"
                                        + original_name_with_extension.replace("/", "_")
                                    )
                                    asset_mapping[new_name] = [
                                        original_name,
                                        original_name_with_extension,
                                    ]

                                for new_name, [
                                    original_name,
                                    original_name_with_extension,
                                ] in asset_mapping.items():
                                    tex_code = tex_code.replace(original_name, new_name)

                                papers.append(tex_code)
                                has_tex_file = True
                            except UnicodeDecodeError:
                                pass
            if has_tex_file:
                num_read += 1

            # Copy the assets
            for new_name, [
                original_name,
                original_name_with_extension,
            ] in asset_mapping.items():
                asset_path = os.path.join(TMP_DIR, original_name_with_extension)
                new_asset_path = os.path.join("data/assets", new_name)
                try:
                    shutil.copy(asset_path, new_asset_path)
                except FileNotFoundError:
                    pass

            # Remove the temporary directory (and its contents)
            shutil.rmtree(TMP_DIR)
        except tarfile.ReadError:
            pass

        # Remove the .tar.gz file
        os.remove(TMP_FILE)

    infos = {
        "num_scrapped": num_scrapped,
        "num_downloaded": num_downloaded,
        "num_extracted": num_extracted,
        "num_read": num_read,
        "num_files": len(papers),
    }
    return papers, infos


def get_asset_names_used(latex_code: str) -> List[str]:
    content, _ = get_delimited_content([latex_code], {})
    list_figures = content["figure"]
    pattern = r"\\includegraphics(?:\[[^\]]+\])?\{([^}]+)\}"

    asset_names = []
    for figure in list_figures:
        matches = re.findall(pattern, figure)
        asset_names.extend(matches)

    return asset_names


def get_delimited_content(
    list_src_code: List[str], infos: dict
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

    for category, delimiters in TEX_DELIMITERS.items():
        delimited_content[category] = []
        for src_code in list_src_code:
            for delimiter in delimiters:
                start, end = delimiter
                start_idx, end_idx = 0, 0
                while start_idx != -1 and end_idx != -1:
                    start_idx = src_code.find(start, end_idx)
                    if start_idx == -1:
                        break
                    end_idx = src_code.find(end, start_idx)
                    if start_idx != -1 and end_idx != -1:
                        delimited_content[category].append(
                            src_code[start_idx : end_idx + len(end)]
                        )

        # Remove duplicates
        original_num = len(delimited_content[category])
        delimited_content[category] = list(set(delimited_content[category]))
        infos[category] = {
            "number_of_original_samples": original_num,
            "number_of_unique_samples": len(delimited_content[category]),
        }

    return delimited_content, infos


def get_and_save_rendering_from_delimited_content(
    delimited_content: Dict[str, List[str]],
    infos: dict,
):
    """Given a dictionnary of delimited content, render all the images.
    Save them directly.

    Args:
        delimited_content (Dict[str, List[str]]): Dictionnary mapping a category to the list of delimited instances
        infos (dict): informations on the scrapping process.
    """

    # Create folder to save the images.
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/images", exist_ok=True)

    for category, list_of_content in delimited_content.items():
        num_instances = len(list_of_content)
        os.makedirs(f"data/images/{category}s", exist_ok=True)
        num_images = 0

        with tqdm(total=num_instances, desc=f"Rendering {category}") as pbar:
            for tex_code in list_of_content:
                try:
                    image, dimensions = latex_to_image(
                        TEX_BEGIN + tex_code + TEX_END,
                        assets_path="data/assets",
                        crop=True,
                    )
                    if image is not None:
                        # Save the image
                        image.save(
                            f"data/images/{category}s/{category}_{num_images}.png"
                        )
                        num_images += 1

                except Exception as e:
                    pass
                pbar.update(1)

        infos[category]["number_of_images"] = num_images
        infos[category]["number_of_images_not_rendered"] = num_instances - num_images

    save_infos(infos)


def save_infos(infos: dict):
    """Save the information about the scrapped papers.

    Args:
        infos (dict): Information about the scrapped papers.
    """
    os.makedirs("data", exist_ok=True)
    with open("data/infos.json", "w") as f:
        json.dump(infos, f, indent=4)


def read_infos() -> dict:
    """Read the information about the scrapped papers.

    Returns:
        dict: Information about the scrapped papers.
    """
    with open("data/infos.json", "r") as f:
        infos = json.load(f)
    return infos


def save_scrapped_papers(papers: List[str], infos: Optional[dict] = None):
    """Save the scrapped papers.

    Args:
        papers (List[str]): List of papers tex codes.
        infos (dict): Information about the scrapped papers.
    """
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/papers", exist_ok=True)
    for i, paper in enumerate(papers):
        with open(f"data/papers/paper_{i}.tex", "w") as f:
            f.write(paper)

    if infos is not None:
        save_infos(infos)


def read_scrapped_papers() -> Tuple[List[str], dict]:
    """Read the scrapped papers.

    Returns:
        List[str]: List of papers tex codes.
        dict: Information about the scrapped papers.
    """
    papers: List[str] = []
    for root, dirs, files in os.walk("data/papers"):
        for file in files:
            if file.endswith(".tex"):
                with open(os.path.join(root, file), "r") as f:
                    try:
                        tex_code = f.read()
                        papers.append(tex_code)
                    except UnicodeDecodeError:
                        pass

    infos = read_infos()
    return papers, infos


def save_delimited_content(
    delimited_content: Dict[str, List[str]], infos: Optional[dict] = None
):
    """Save the equations.

    Args:
        delimited_content (Dict[str, List[str]]): Dictionnary mapping a category to the list of delimited instances
    """
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/contents", exist_ok=True)

    for category, content in delimited_content.items():
        os.makedirs(f"data/contents/{category}s", exist_ok=True)
        for i, tex_code in enumerate(content):
            with open(f"data/contents/{category}s/{category}_{i}.tex", "w") as f:
                f.write(tex_code)
    if infos is not None:
        save_infos(infos)


def read_delimited_content() -> Tuple[Dict[str, List[str]], dict]:
    """Read the equations.

    Returns:
        Dict[str, List[str]]: Dictionnary mapping a category to the list of delimited instances
        dict: Information about the scrapped papers.
    """
    delimited_content: Dict[str, List[str]] = {}

    data_folder = "data/contents"
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

    infos = read_infos()
    return delimited_content, infos


if __name__ == "__main__":
    # Check if data/papers exists
    if os.path.exists("data/images"):
        print("Images already exist.")
    else:
        if os.path.exists("data/contents"):
            print("Delimited content already exist.")
            delimited_content, infos = read_delimited_content()
            delimited_content["equation"] = []
        else:
            if os.path.exists("data/papers"):
                print("Papers already exist.")
                papers, infos = read_scrapped_papers()
            else:
                print("Scrapping papers...")
                papers, infos = gather_papers()
                save_scrapped_papers(papers, infos)
            delimited_content, infos = get_delimited_content(papers, infos)
            delimited_content["equation"] = []
            save_delimited_content(delimited_content, infos)
        get_and_save_rendering_from_delimited_content(delimited_content, infos)
