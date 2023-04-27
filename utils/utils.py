import os


def list_files(directory: str, file_ext: str = ".py") -> list:
    """
    List all files in the given directory (recursively)
    """
    filenames = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(file_ext):
                filenames.append(os.path.join(root, filename))

    return filenames


def read_file(filename: str) -> str:
    """
    Open a file and return its contents as a string
    """
    with open(filename) as file:
        return file.read()


def prep_tar(tarfile: str):
    """
        prepare for the target dir
    """
    processed_project_dir = os.path.join(tarfile, "processed_projects")
    avl_types_dir = os.path.join(tarfile, "extracted_visible_types")
    if not os.path.exists(tarfile):
        os.mkdir(tarfile)
        if not os.path.exists(processed_project_dir):
            os.mkdir(processed_project_dir)
        if not os.path.exists(avl_types_dir):
            os.mkdir(avl_types_dir)
    else:
        if not os.path.exists(processed_project_dir):
            os.mkdir(processed_project_dir)
        if not os.path.exists(avl_types_dir):
            os.mkdir(avl_types_dir)
    return processed_project_dir,avl_types_dir


