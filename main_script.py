import os
from shutil import copy
import json
import time
from functools import wraps

class PathObj:
    """
    Path object. Used to check, store and handle paths.
    copy_from_path: The source folder
    final_destination_path: The target folder
    """
    gathered_paths = list()
    path_correspondence = dict()

    def __init__(self, given_path: str, default_path: str):
        self.copy_from_path = given_path
        self.default_path = default_path
        self.final_destination_path = os.path.join(self.default_path, self.copy_from_path.split("\\")[-1]) if \
            self.copy_from_path.split("\\")[-1] != "" else os.path.join(self.default_path,
                                                                        self.copy_from_path.split("\\")[-2])

    # Logger wrapper. Generates a log file with the time and functions ran
    def logger_w(msg):
        def logger(func):
            # @wraps(func)
            def wrapper(inst, *args, **kwargs):
                wrapped_fun = func(inst, *args, **kwargs)
                with open("log.txt", 'a') as log:
                    named_tuple = time.localtime()
                    time_string = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
                    log.write(time_string + " - " + msg + "\n")
                return wrapped_fun
            return wrapper
        return logger

    # Handle the existence of the path
    @logger_w(msg="The check_path_existence ran!")
    def check_path_existence(self) -> list[bool]:
        if not os.path.exists(self.final_destination_path):
            os.mkdir(self.final_destination_path, mode=0o777)
            print(f"Directory {self.final_destination_path} does not exist. Creating now...")
            return [True, True]
        elif os.path.exists(self.final_destination_path) and len(os.listdir(self.final_destination_path)) == 0:
            print(f"Directory {self.final_destination_path} exists but it is empty. This will be used further.")
            return [True, False]
        else:
            print(f"Directory {self.final_destination_path} exists and has contents. This will not be synchronized.")
            return [False, False]

    # Gather the largest file in the source folder by extension
    @logger_w(msg="The gather_largest_file ran!")
    def gather_largest_file(self, extension: str) -> os.path:
        max_size = float(0)
        old_max_size = 0
        max_file_in_folder = ""
        for file in os.listdir(self.copy_from_path):
            if extension in os.path.splitext(file)[1]:
                current_file = os.path.join(self.copy_from_path, file)
                max_size = max_size if os.path.getsize(current_file) < max_size else os.path.getsize(current_file)
                if old_max_size != max_size:
                    max_file_in_folder = current_file
                    old_max_size = max_size

        return max_file_in_folder

    # Gather a limited or unlimited amount of files that contain a keyword from the folder.
    @logger_w(msg="The gather_special_files ran!")
    def gather_special_files(self, keyword: str, *args) -> list:
        special_files = list()
        try:
            limit = args[0]
            print(f"Files that contain {keyword} will be limited to {str(limit)} items...")
        except IndexError:
            limit = -1
        for file in os.listdir(self.copy_from_path):
            if keyword in file.split("\\")[-1]:
                special_files.append(os.path.join(self.copy_from_path, file))
                limit -= 1
            if limit == 0:
                break

        return special_files

    # Updates gathered source paths
    @logger_w(msg="The update_gathered_paths ran!")
    def update_gathered_paths(self):
        PathObj.gathered_paths.append(self.copy_from_path)
        return PathObj.gathered_paths

    # Updates the correspondence dictionary
    @logger_w(msg="The update_path_correspondence ran!")
    def update_path_correspondence(self, *args):
        PathObj.path_correspondence[self.final_destination_path] = [*args]
        return PathObj.path_correspondence

    # Copies the stored largest file
    @logger_w(msg="The copy_largest_file ran!")
    def copy_largest_file(self):
        item = self.final_destination_path
        source = PathObj.path_correspondence[item][0]
        destination = item
        copy(source, destination)
        print(f"Copied {source} to {destination}")
        return print("Copy success!")

    # Copies the stored special files
    @logger_w(msg="The copy_special_files ran!")
    def copy_special_files(self):
        item = self.final_destination_path
        source_list = PathObj.path_correspondence[item][1]
        if len(source_list) != 0:
            for j in range(len(source_list)):
                source = source_list[j]
                destination = item
                copy(source, destination)
                print(f"Copied {source} to {destination}")
        return print("Multi-Copy success!")

    def __str__(self):
        return f"Objects inside of the path: {self.path_correspondence}"

    def __repr__(self):
        return f"\nGiven path {self.copy_from_path}\nCopy-To Path {self.final_destination_path}"


class JsonParser:
    """
    Used to read a json file.
    It must contain a key pair of strings.
    The destination has to be one of the keys.
    The other keys should contain 'path' to be considered
    """
    def __init__(self, json_file):
        self.json_file = json_file

    # Return a py readable dictionary
    def parse_json(self) -> dict:
        with open(self.json_file, 'r') as j:
            data = json.load(j)
        return data

    # Return the given JSON destination along with a curated path dictionary
    @staticmethod
    def extract_destination(data: dict) -> list:
        j_destination = data["destination"]
        j_dict_copy = data.copy()
        del j_dict_copy["destination"]
        return [j_destination, j_dict_copy]


def main():
    obj = JsonParser("paths_to_sync.json")
    j_dict = obj.parse_json()
    extracted_dst, parsed_json_dict = JsonParser.extract_destination(j_dict)
    roll_list = [x for x in parsed_json_dict.keys() if "path" in x]
    for item in roll_list:
        item = parsed_json_dict[item]
        path_obj = PathObj(item, extracted_dst)
        bool_list = path_obj.check_path_existence()
        if (bool_list[0] and bool_list[1]) or (bool_list[0] and not bool_list[1]):
            path_obj.update_gathered_paths()
            extension = ".txt"
            special_text = "test"
            largest_file = path_obj.gather_largest_file(extension)
            special_objects = path_obj.gather_special_files(special_text, 10)
            path_obj.update_path_correspondence(largest_file, special_objects)
            print(str(path_obj))
            if PathObj.path_correspondence[path_obj.final_destination_path][0] != '':
                path_obj.copy_largest_file()
            else:
                print(f"Files with {extension} extension not found ")
            if PathObj.path_correspondence[path_obj.final_destination_path][1]:
                path_obj.copy_special_files()
            else:
                print(f"Files with {special_text} in the name not found ")
        else:
            print("Given path will be skipped...")


if __name__ == "__main__":
    main()

