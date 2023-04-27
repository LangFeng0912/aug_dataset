import json

from libsa4py.cst_extractor import Extractor
import utils.pyre as pyre_util
from utils.utils import list_files, read_file, prep_tar
import argparse
import os
from pathlib import Path


# pyre start pipeline
def pyre_start(project_path):
    pyre_util.clean_watchman_config(project_path)
    pyre_util.clean_pyre_config(project_path)
    pyre_util.start_watchman(project_path)
    pyre_util.start_pyre(project_path)


def process_project(project_path, tar_path):
    project_author = project_path.split("/")[len(project_path.split("/")) - 2]
    project_name = project_path.split("/")[len(project_path.split("/")) - 1]

    id_tuple = (project_author, project_name)
    project_id = "/".join(id_tuple)
    project_analyzed_files: dict = {project_id: {"src_files": {}, "type_annot_cove": 0.0}}
    print(f'Running pipeline for project {project_path}')

    pyre_start(project_path)
    # start pyre infer for project
    print(f'Running pyre infer for project {project_path}')
    pyre_util.pyre_infer(project_path)

    print(f'Extracting for {project_path}...')
    project_files = list_files(project_path)
    extracted_avl_types = None
    print(f"{project_path} has {len(project_files)} files")

    project_files = [(f, str(Path(f).relative_to(Path(project_path).parent))) for f in project_files]

    if len(project_files) != 0:
        print(f'Running pyre query for project {project_path}')
        for filename, f_relative in project_files:
            pyre_data_file = pyre_util.pyre_query_types(project_path, filename)
            # extract types
            project_analyzed_files[project_id]["src_files"][filename] = \
                Extractor.extract(read_file(filename), pyre_data_file).to_dict()
            # extract available types
            extracted_avl_types = project_analyzed_files[project_id]["src_files"][filename]['imports'] + \
                                  [c['name'] for c in
                                   project_analyzed_files[project_id]["src_files"][filename]['classes']]

    print(f'Saving available type hints for {project_id}...')
    processed_project_dir, avl_types_dir = prep_tar(tar_path)

    if avl_types_dir is not None:
        if extracted_avl_types:
            with open(os.path.join(avl_types_dir, f'{project_author}_{project_name}_avltypes.txt'),
                      'w') as f:
                for t in extracted_avl_types:
                    f.write("%s\n" % t)

    if len(project_analyzed_files[project_id]["src_files"].keys()) != 0:
        project_analyzed_files[project_id]["type_annot_cove"] = \
            round(sum([project_analyzed_files[project_id]["src_files"][s]["type_annot_cove"] for s in
                       project_analyzed_files[project_id]["src_files"].keys()]) / len(
                project_analyzed_files[project_id]["src_files"].keys()), 2)

        processed_file = os.path.join(processed_project_dir, f"{project_author}{project_name}.json")
        with open(processed_file, 'w') as json_f:
            json.dump(project_analyzed_files, json_f, indent=4)

    # pyre shutdown
    pyre_util.pyre_server_shutdown(project_path)



def main():
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument("--p", required=True, type=str, help="Path to Python projects")
    parser.add_argument("--o", required=True, type=str, help="Path to store JSON-based processed projects")
    args = parser.parse_args()
    project_path = args.p
    tar_path = args.o
    process_project(project_path, tar_path)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

