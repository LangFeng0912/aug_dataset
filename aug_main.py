import json

from libsa4py.cst_extractor import Extractor
from libsa4py.cst_transformers import TypeApplier
from libsa4py.exceptions import ParseError
from libsa4py.utils import write_file, list_files, read_file
import utils.pyre as pyre_util
import argparse
import os
from pathlib import Path
import time
from datetime import timedelta
import libcst as cst
from tqdm import tqdm


# pyre start pipeline
def pyre_start(project_path):
    pyre_util.clean_watchman_config(project_path)
    pyre_util.clean_pyre_config(project_path)
    pyre_util.start_watchman(project_path)
    pyre_util.start_pyre(project_path)


def process_project(project_path):
    start_t = time.time()
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
        try:
            for filename, f_relative in tqdm(project_files):
                # print(filename)
                pyre_data_file = pyre_util.pyre_query_types(project_path, filename)
                # extract types
                project_analyzed_files[project_id]["src_files"][filename] = \
                    Extractor.extract(read_file(filename), pyre_data_file).to_dict()
        except ParseError as err:
            pass
        except UnicodeDecodeError:
            pass
        except Exception as err:
            pass

    # pyre shutdown
    pyre_util.pyre_server_shutdown(project_path)
    pyre_util.clean_config(project_path)
    print(f'inplace augmention for {project_id}...')
    proj_json = project_analyzed_files
    for p in proj_json.keys():
        for i, (f, f_d) in enumerate(proj_json[p]['src_files'].items()):
            f_read = read_file(f)
            if len(f_read) != 0:
                try:
                    f_parsed = cst.parse_module(f_read)
                    try:
                        f_parsed = cst.metadata.MetadataWrapper(f_parsed).visit(TypeApplier(f_d, True))
                        write_file(f, f_parsed.code)
                    except KeyError as ke:
                        pass
                    except TypeError as te:
                        pass
                except cst._exceptions.ParserSyntaxError as pse:
                    pass
    print("Finished processing project in %s " % str(timedelta(seconds=time.time()-start_t)))



def main():
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument("--p", required=True, type=str, help="Path to Python projects")
    # parser.add_argument("--o", required=false, type=str, help="Path to augmented Python projects")
    args = parser.parse_args()
    project_path = args.p
    # tar_path = args.o
    process_project(project_path)

if __name__ == '__main__':
    main()
