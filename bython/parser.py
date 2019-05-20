import re
import os

"""
Python module for converting bython code to python code.
"""

def _ends_in_by(word):
    """
    Returns True if word ends in .by, else False

    Args:
        word (str):     Filename to check

    Returns:
        boolean: Whether 'word' ends with 'by' or not
    """
    return word[-3:] == ".by"


def _change_file_name(name, outputname=None):
    """
    Changes *.by filenames to *.py filenames. If filename does not end in .by, 
    it adds .py to the end.

    Args:
        name (str):         Filename to edit
        outputname (str):   Optional. Overrides result of function.

    Returns:
        str: Resulting filename with *.py at the end (unless 'outputname' is
        specified, then that is returned).
    """

    # If outputname is specified, return that
    if outputname is not None:
        return outputname

    # Otherwise, create a new name
    if _ends_in_by(name):
        return name[:-3] + ".py"

    else:
        return name + ".py"


def parse_imports(filename):
    """
    Reads the file, and scans for imports. Returns all the assumed filename
    of all the imported modules (ie, module name appended with ".by")

    Args:
        filename (str):     Path to file

    Returns:
        list of str: All imported modules, suffixed with '.by'. Ie, the name
        the imported files must have if they are bython files.
    """
    infile = open(filename, 'r')
    infile_str = ""

    for line in infile:
        infile_str += line


    imports = re.findall(r"(?<=import\s)[\w.]+(?=;|\s|$)", infile_str)
    imports2 = re.findall(r"(?<=from\s)[\w.]+(?=\s+import)", infile_str)

    imports_with_suffixes = [im + ".by" for im in imports + imports2]

    return imports_with_suffixes


def parse_file(filepath, add_true_line, filename_prefix, outputname=None, change_imports=None):
    """
    Converts a bython file to a python file and writes it to disk.

    Args:
        filename (str):             Path to the bython file you want to parse.
        add_true_line (boolean):    Whether to add a line at the top of the
                                    file, adding support for C-style true/false
                                    in addition to capitalized True/False.
        filename_prefix (str):      Prefix to resulting file name (if -c or -k
                                    is not present, then the files are prefixed
                                    with a '.').
        outputname (str):           Optional. Override name of output file. If
                                    omitted it defaults to substituting '.by' to
                                    '.py'    
        change_imports (dict):      Names of imported bython modules, and their 
                                    python alternative.
    """
    filename = os.path.basename(filepath)
    filedir = os.path.dirname(filepath)

    infile = open(filepath, 'r')
    outfile = open(filename_prefix + _change_file_name(filename, outputname), 'w')

    indentation_level = 0
    indentation_sign = "    "

    if add_true_line:
        outfile.write("true=True; false=False;\n")

    # Read file to string
    infile_str_raw = ""
    for line in infile:
        infile_str_raw += line

    # Add 'pass' where there is only a {}. 
    # 
    # DEPRECATED FOR NOW. This way of doing
    # it is causing a lot of problems with {} in comments. The feature is removed
    # until I find another way to do it. 
    
    # infile_str_raw = re.sub(r"{[\s\n\r]*}", "{\npass\n}", infile_str_raw)

    # Fix indentation
    infile_str_indented = ""
    for line in infile_str_raw.split("\n"):
        # Search for comments, and remove for now. Re-add them before writing to
        # result string
        m = re.search(r"[ \t]*([(\/\/)#].*$)", line)

        # Make sure # sign is not inside quotations. Delete match object if it is
        if m is not None:
            m2 = re.search(r"[\"'].*[(\/\/)#].*[\"']", m.group(0))
            if m2 is not None:
                m = None

        if m is not None:
            add_comment = m.group(0)
            line = re.sub(r"[ \t]*([(\/\/)#].*$)", "", line)
        else:
            add_comment = ""
        
        # replace // with #
        add_comment = add_comment.replace("//", "#", 1)

        # skip empty lines:
        if line.strip() in ('\n', '\r\n', ''):
            infile_str_indented += indentation_level*indentation_sign + add_comment.lstrip() + "\n"
            continue

        # remove existing whitespace:
        line = line.lstrip()
        
        # Check for reduced indent level
        for i in list(line):
            if i == "}":
                indentation_level -= 1

        # Add indentation
        for i in range(indentation_level):
            line = indentation_sign + line

        # Check for increased indentation
        for i in list(line):
            if i == "{":
                indentation_level += 1

        # Replace { with : and remove }
        line = re.sub(r"[\t ]*{[ \t]*", ":", line)
        line = re.sub(r"}[ \t]*", "", line)
        line = re.sub(r"\n:", ":", line)

        infile_str_indented += line + add_comment + "\n"


    # Support for extra, non-brace related stuff
    infile_str_indented = re.sub(r"else\s+if", "elif", infile_str_indented)
    infile_str_indented = re.sub(r";\n", "\n", infile_str_indented)

    # Change imported names if necessary
    if change_imports is not None:
        for module in change_imports:
            infile_str_indented = re.sub("(?<=import\\s){}".format(module), "{} as {}".format(change_imports[module], module), infile_str_indented)
            infile_str_indented = re.sub("(?<=from\\s){}(?=\\s+import)".format(module), change_imports[module], infile_str_indented)

    outfile.write(infile_str_indented)

    infile.close()
    outfile.close()


def remove_indentation(code):
    code = re.sub(r"^[ \t]*", "", code, 1)
    code = re.sub(r"\r?\n[ \t]+", "\n", code)
    return code


def prepare_braces(code):
    # TODO fix issue with brace within comments
    code = re.sub(r"[ \t]*\{", "{", code)
    code = re.sub(r"[ \t]*(\/\/.*)?(\#.*)?\r?\n[ \t]*{", "{", code)
    code = re.sub(r"\{", "{\n", code)
    return code


def remove_empty_lines(code):
    code = re.sub(r"\r?\n[ \t]*(\r?\n[ \t]*)+", "\n", code)
    return code


def indent_if_newline(code, outfile, indentation, indentation_str):
    if code == "\n":
        #print(identation, end="")
        for x in range(indentation):
            outfile.write(indentation_str)


def parse_file_recursive(filepath, add_true_line=False, filename_prefix="", outputname=None, change_imports=None):
    """
    Converts a bython file to a python file recursively and writes it to disk.

    Args:
        filename (str):             Path to the bython file you want to parse.
        add_true_line (boolean):    Whether to add a line at the top of the
                                    file, adding support for C-style true/false
                                    in addition to capitalized True/False.
        filename_prefix (str):      Prefix to resulting file name (if -c or -k
                                    is not present, then the files are prefixed
                                    with a '.').
        outputname (str):           Optional. Override name of output file. If
                                    omitted it defaults to substituting '.by' to
                                    '.py'    
        change_imports (dict):      Names of imported bython modules, and their 
                                    python alternative.
    """

    # TODO remove defaults for the parameters 'add_true_line' and 'filename_prefix'
    # i've put them there for ease of use

    # inner function for parsing recursively
    def recursive_parser(code, position, scope, outfile, indentation, indentation_str="    "):

        # scope equal to "" means it's on global scope
        # scope equal to "{" means it's on local scope
        if scope == "" or scope == "{":

            if scope == "":
                print("g", end="") # for debugging
            else:
                indentation = indentation + 1

            while position < len(code):

                # check for brace opening
                if code[position] == "{":
                    print("{", end="") # for debugging
                    outfile.write(":")
                    position = recursive_parser(code, position + 1, "{", outfile, indentation + 1, indentation_str)
                    if scope == "":
                        print("g", end="") # for debugging

                # check for python-style comment
                elif code[position] == "#":
                    outfile.write(code[position])
                    position = recursive_parser(code, position + 1, "#", outfile, indentation, indentation_str)
                
                # check for c and cpp-style comment
                elif code[position] == "/":
                    if code[position + 1] == "/":
                        outfile.write("#")
                        position = recursive_parser(code, position + 2, "//", outfile, indentation, indentation_str)
                    elif code[position + 1] == "*":
                        outfile.write(code[position:position+2]) # TODO implement comment on all lines
                        position = recursive_parser(code, position + 2, "/*", outfile, indentation, indentation_str)
                
                # check for single-quote string start
                elif code[position] == "\'":
                    outfile.write(code[position])
                    position = recursive_parser(code, position + 1, "\'", outfile, indentation, indentation_str)

                # check for double-quote string start
                elif code[position] == "\"":
                    outfile.write(code[position])
                    position = recursive_parser(code, position + 1, "\"", outfile, indentation, indentation_str)
                
                # check for equals (for python dicts with braces)
                elif code[position] == "=":
                    outfile.write(code[position])
                    position = recursive_parser(code, position + 1, "=", outfile, indentation, indentation_str)

                # check for brace closing (when not on global)
                elif scope == "{":
                    if code[position] == "}":
                        print("}", end="")
                        return position + 1
                    else:
                        outfile.write(code[position])
                        indent_if_newline(code[position], outfile, indentation, indentation_str)
                        position = position + 1

                else:
                    outfile.write(code[position])
                    indent_if_newline(code[position], outfile, indentation, indentation_str)
                    position = position + 1

        elif scope == "#":
            print("#", end="") # for debugging
            while position < len(code):
                outfile.write(code[position])
                indent_if_newline(code[position], outfile, indentation, indentation_str)
                if code[position] == "\n":
                    print("n", end="") # for debugging
                    return position + 1

                else:
                    position = position + 1
        
        elif scope == "//":
            print("//", end="") # for debugging
            while position < len(code):
                outfile.write(code[position])
                indent_if_newline(code[position], outfile, indentation, indentation_str)
                if code[position] == "\n":
                    print("n", end="") # for debugging
                    return position + 1

                else:
                    position = position + 1
        
        elif scope == "/*":
            print("/*", end="") # for debugging
            while position < len(code):
                outfile.write(code[position])
                indent_if_newline(code[position], outfile, indentation, indentation_str)
                # check for c-style comment closing
                if code[position] == "*":
                    if code[position + 1] == "/":
                        outfile.write(code[position + 1]) # TODO remove
                        print("*/", end="") # for debugging
                        return position + 2

                else:
                    position = position + 1

        elif scope == "\'":
            print("\'^", end="") # for debugging
            while position < len(code):
                outfile.write(code[position])
                indent_if_newline(code[position], outfile, indentation, indentation_str)
                # check for single-quote string ending
                if code[position] == "\'":
                    # check if its escaped
                    if code[position - 1] != "\\":
                        print("$\'", end="") # for debugging
                        return position + 1
                    else:
                        position = position + 1

                else:
                    position = position + 1
        
        elif scope == "\"":
            print("\"^", end="") # for debugging
            while position < len(code):
                outfile.write(code[position])
                indent_if_newline(code[position], outfile, indentation, indentation_str)
                # check for single-quote string ending
                if code[position] == "\"":
                    # check if its escaped
                    if code[position - 1] != "\\":
                        print("$\'", end="") # for debugging
                        return position + 1
                    else:
                        position = position + 1

                else:
                    position = position + 1
        
        elif scope == "=":
            indentation = indentation + 1
            print("=", end="") # for debugging
            while position < len(code):
                # check for dicts
                if code[position] == "{":
                    outfile.write(code[position])
                    indent_if_newline(code[position], outfile, indentation, indentation_str)
                    print(".dict.", end="") # for debugging
                    return recursive_parser(code, position + 1, "={", outfile, indentation + 1, indentation_str)

                # check for non dicts
                elif re.search(r"[^\s\n\r]", code[position]):
                    outfile.write(code[position])
                    indent_if_newline(code[position], outfile, indentation, indentation_str)
                    print("!", end="") # for debugging
                    return position

                else:
                    outfile.write(code[position])
                    indent_if_newline(code[position], outfile, indentation, indentation_str)
                    position = position + 1
        
        elif scope == "={":
            while position < len(code):
                
                if code[position] == "}":
                    outfile.write(code[position])
                    indent_if_newline(code[position], outfile, indentation - 1, indentation_str)
                    return position + 1

                else:
                    outfile.write(code[position])
                    indent_if_newline(code[position], outfile, indentation, indentation_str)
                    position = position + 1

        else:
            raise Exception("invalid scope was reached")


    filename = os.path.basename(filepath)
    filedir = os.path.dirname(filepath)

    infile = open(filepath, 'r')
    infile_str = infile.read()
    infile.close()

    outfile = open(filename_prefix + _change_file_name(filename, outputname), 'w')

    infile_str = remove_indentation(infile_str)
    infile_str = prepare_braces(infile_str)
    infile_str = remove_empty_lines(infile_str)

    # TODO remove
    filteredfile = open(filename + ".filtered", 'w')
    filteredfile.write(infile_str)
    filteredfile.close()

    recursive_parser(infile_str, 0, "", outfile, 0, "    ")

    outfile.close()