import arxivscraper
from urllib.request import urlretrieve
import tarfile
import os
from typing import List, Optional, Tuple
from tqdm import tqdm
import shutil
import json
from PIL import Image

from constants import TEX_EQUATION_DELIMITER, TEX_BEGIN, TEX_END
from renderer import latex_to_image


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

            # Search for all '.tex' file in the extracted directory
            has_tex_file = False
            for root, dirs, files in os.walk(TMP_DIR):
                for file in files:
                    if file.endswith(".tex"):
                        with open(os.path.join(root, file), "r") as f:
                            try:
                                tex_code = f.read()
                                papers.append(tex_code)
                                has_tex_file = True
                            except UnicodeDecodeError:
                                pass
            if has_tex_file:
                num_read += 1

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


def get_equations(list_src_code: List[str], infos: dict) -> Tuple[List[str], dict]:
    """Given a tex source code, return a list of equations.

    Args:
        list_src_code (List[str]): List of tex source codes.
        infos (dict): informations on the scrapping process.

    Returns:
        List[str]: List of equations.
        infos (dict): informations added.
    """
    num_lines_of_code = sum([len(src_code.split("\n")) for src_code in list_src_code])
    num_delimiters = len(TEX_EQUATION_DELIMITER)
    equations: List[str] = []

    with tqdm(
        total=num_lines_of_code * num_delimiters, desc="Extracting equations"
    ) as pbar:
        for src_code in list_src_code:
            for delimiter in TEX_EQUATION_DELIMITER:
                start, end = delimiter
                start_idx, end_idx, last_end_idx = 0, 0, 0
                while start_idx != -1 and end_idx != -1:
                    start_idx = src_code.find(start, end_idx)
                    if start_idx == -1:
                        break
                    end_idx = src_code.find(end, start_idx)
                    if start_idx != -1 and end_idx != -1:
                        equations.append(src_code[start_idx : end_idx + len(end)])
                        pbar.update(end_idx - last_end_idx)
                        last_end_idx = end_idx
                pbar.update(len(src_code) - last_end_idx)

    num_eq = len(equations)
    equations = list(set(equations))
    infos["num_equations"] = len(equations)
    infos["num_equations_duplicated"] = num_eq - len(equations)

    return equations, infos


def get_images_from_equations(
    equations: List[str],
    infos: dict,
) -> Tuple[List["Image"], dict]:
    """Given a list of equations, return a list of images.

    Args:
        equations (List[str]): List of equations.
        infos (dict): informations on the scrapping process.

    Returns:
        List[str]: List of images.
        infos (dict): informations added.
    """
    images: List[str] = []
    num_equations = len(equations)

    with tqdm(total=num_equations, desc="Rendering equations") as pbar:
        for equation in equations:
            try:
                image, dimensions = latex_to_image(
                    TEX_BEGIN + equation + TEX_END,
                    assets_path="assets",
                    crop=True,
                )
                if image is not None:
                    images.append(image)
            except Exception as e:
                pass
            pbar.update(1)

    infos["num_images"] = len(images)
    infos["num_images_failed"] = num_equations - len(images)

    return images, infos


def save_infos(infos: dict):
    """Save the information about the scrapped papers.

    Args:
        infos (dict): Information about the scrapped papers.
    """
    os.makedirs("data", exist_ok=True)
    with open("data/infos.json", "w") as f:
        json.dump(infos, f)


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


def save_equations(equations: List[str], infos: Optional[dict] = None):
    """Save the equations.

    Args:
        equations (List[str]): List of equations.
    """
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/equations", exist_ok=True)
    for i, equation in enumerate(equations):
        with open(f"data/equations/equation_{i}.tex", "w") as f:
            f.write(equation)
    if infos is not None:
        save_infos(infos)


def read_equations() -> Tuple[List[str], dict]:
    """Read the equations.

    Returns:
        List[str]: List of equations.
        dict: Information about the scrapped papers.
    """
    equations: List[str] = []
    for root, dirs, files in os.walk("data/equations"):
        for file in files:
            if file.endswith(".tex"):
                with open(os.path.join(root, file), "r") as f:
                    try:
                        tex_code = f.read()
                        equations.append(tex_code)
                    except UnicodeDecodeError:
                        pass
    infos = read_infos()
    return equations, infos


def save_images(images: List["Image"], infos: Optional[dict] = None):
    """Save the images.

    Args:
        images (List[Image]): List of images.
    """
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/images", exist_ok=True)
    for i, image in enumerate(images):
        image.save(f"data/images/image_{i}.png")
    if infos is not None:
        save_infos(infos)


def read_images() -> Tuple[List["Image"], dict]:
    """Read the images.

    Returns:
        List[Image]: List of images.
        dict: Information about the scrapped papers.
    """
    images: List["Image"] = []
    for root, dirs, files in os.walk("data/images"):
        for file in files:
            if file.endswith(".png"):
                image = Image.open(os.path.join(root, file))
                images.append(image)
    infos = read_infos()
    return images, infos


if __name__ == "__main__":
    # Check if data/papers exists
    if os.path.exists("data/images"):
        print("Images already exist.")
        images, infos = read_images()
    else:
        if os.path.exists("data/equations"):
            print("Equations already exist.")
            equations, infos = read_equations()
        else:
            if os.path.exists("data/papers"):
                print("Papers already exist.")
                papers, infos = read_scrapped_papers()
            else:
                print("Scrapping papers...")
                papers, infos = gather_papers()
                save_scrapped_papers(papers, infos)
            equations, infos = get_equations(papers, infos)
            save_equations(equations, infos)
        images, infos = get_images_from_equations(equations, infos)
        save_images(images, infos)
