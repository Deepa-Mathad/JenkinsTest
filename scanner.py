# Python script that handles clang-tidy execution

import os
import json
import subprocess

# return a list of tracked files that belong to the given git repository
def get_tracked_files(git_dir):
    # get list of files in a list of strings
    command = "cd " + git_dir + "; " + "git ls-tree -r HEAD --name-only"
    ret = subprocess.run(command, capture_output=True, shell=True, 
                            encoding='utf-8')

    files = ret.stdout.splitlines()
    # construct absolut path of files
    files = list(map(lambda file: os.path.abspath(git_dir + "/" + file), files))

    # return files
    return files

# return a list of compile_commands that has its files tracked in the given git repository
def filter_commands_by_submodule(compile_commands, git_dir):
    files = get_tracked_files(git_dir)

    return [command for command in compile_commands
                        if command['file'] in files]

# loads compile_commands.json from the f360_path. 
# Filter items using multiple criterias, by git submodule and ignore list
def load_compile_commands(f360_path, submodules_list, ignore_paths, compile_commands_path):
    file = open(compile_commands_path)
    compile_commands = json.load(file)

    # Keep items that are not in ignore_list
    if ignore_paths:
        compile_commands = [compileCommandsIterator for compileCommandsIterator in compile_commands
                    if not any([pathIterator in compileCommandsIterator['file'] 
                                for pathIterator in ignore_paths])]

    # Keep items that are only in submodule list
    if submodules_list:
        new_compile_commands = None
        for submodule in submodules_list:
            submodule_commands = (filter_commands_by_submodule(compile_commands, f360_path + "/" + submodule))
            
            if new_compile_commands is None:
                new_compile_commands = submodule_commands
            else:
                for cmd in submodule_commands:
                    new_compile_commands.append(cmd)

        return new_compile_commands
    
    return compile_commands

def create_tmp_compile_commands(compile_commands):
    filePath = os.getcwd() + "/"
    # Serializing json
    json_object = json.dumps(compile_commands, indent=4)
 
    # Writing to tmp_compile_commands.json
    with open("compile_commands.json", "w") as outfile:
        outfile.write(json_object)
        filePath = filePath + outfile.name

    return filePath

# Initialize configuration for scanner
def init_config(f360_path, clang_path, commands_path, no_workers):
    if clang_path is None:
        clang_path = os.getcwd()

    if os.path.isabs(clang_path) is not True:
        clang_path = os.getcwd() + "/" + clang_path

    # Configure paths for clang_static_analyzer    
    # Paths for local install
    clang_tidy_bin = clang_path + "/bin/clang-tidy"
    clang_tidy_py = clang_path + "/bin/run-clang-tidy"
    clang_diff_py = clang_path + "/share/clang/clang-tidy-diff.py"

    # Paths for local build
    #clang_tidy_bin = clang_path + "/build/Release/bin/clang-tidy"
    #clang_tidy_py = clang_path + "/clang-tools-extra/clang-tidy/tool/run-clang-tidy.py"
    #clang_diff_py = clang_path + "/clang-tools-extra/clang-tidy/tool/clang-tidy-diff.py"

    # Use single thread if workers are not specified
    if no_workers is None:
        no_workers = 1
    
    # Use compile_commands from fusion360 output folder if commands_path is not specified
    if commands_path is None:
        commands_path = f360_path + "/Output/MAC64/compile_commands.json"

    return {
        'clang_tidy_bin' : clang_tidy_bin,
        'clang_tidy_py'  : clang_tidy_py,
        'clang_diff_py'  : clang_diff_py,
        'no_workers'     : no_workers,
        'cmd_path'       : commands_path
    }

def start_scanner(f360_path, clang_static_analyzer_path, compile_commands_path, tidy_config, no_workers, pr, submodules, ignore_paths, regex):
    config = init_config(f360_path, clang_static_analyzer_path, compile_commands_path, no_workers)

    if submodules is not None:
        new_commands = load_compile_commands(f360_path, submodules, ignore_paths, config['cmd_path'])
        new_commands_path = create_tmp_compile_commands(new_commands)
        config['cmd_path'] = new_commands_path

    if pr is not None:
        command = "cat " + pr + " | "
        command = command + "python " + config['clang_diff_py'] + " "       \
                + "-p1" + " "                                               \
                + "-j" + str(config['no_workers']) + " "                    \
                + "-clang-tidy-binary=" + config['clang_tidy_bin'] + " "    \
                + "-path=" + os.getcwd() + " "                              \
                + "-checks=" + "-*,fusion-qwidget" + " "

    else:
        command = "python " + config['clang_tidy_py']  + " "                \
                + "-j" + str(config['no_workers']) + " "                    \
                + "-clang-tidy-binary=" + config['clang_tidy_bin'] + " "    \
                + "-p=" + os.getcwd() + " "                                 \
                + "-checks=" + "-*,fusion-qwidget" + " "

    # Ignore ip, port and regex if tiny_config is present
    if tidy_config is not None:
        command = command + "-config-file=" + tidy_config
    else:
        if regex is not None:
            command = command + "-header-filter=\"" + regex + "\" "


    # Execute command
    print(command)
    os.chdir(f360_path)
    os.system(command)
