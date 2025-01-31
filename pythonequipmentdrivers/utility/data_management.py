from pathlib import Path
from time import strftime
import json
from itertools import zip_longest
from typing import Iterable, Optional


def log_data(file_path: Path, *data, init=False):
    """
    log_data(file_path, *data, init=False)

    Writes an iterable to a row of a csv file. Useful for logging data row by
    row while a test or measurement is in progress.

    If init=True a new file is created (or overwriten if the file already
    exists) and the iterable "data" is unpacked into the first row of the new
    document. If init = False then the existing file is opened and the iterable
    "data" is unpacked and appended to the end of the document. If init = False
    but the file does not already exist it will be created.

    The arguement "file_path" specifies the path of the file to be
    created/updated. The log file will be storted at file_path.csv
    , file_path itself does not need to contain the file extension, it will
    automatically be added.

    The iterable "data" can contain an arbitrary number of elements and each
    element can use an arbitrary data type as long as it can be safely cast to
    a string. The argument "data" should be passed as an unpacked structure,
    not as an iterable. For example:

        Correct:
            log_data("my_data", 1, 2, 3, 4, 5)
            log_data("my_data", *list_of_data)
            log_data("my_data", *['a', 'b', 'c', 4, 5, 6])
            log_data("my_data", *(1, 2, 3, 4, 5))
            log_data("my_data", 'column 1', 'column 2', init=True)

        Incorrect:
            log_data("my_data", [1, 2, 3, 4, 5])
            log_data("my_data", ('a', 'b', 'c', 'd'))

    In the case of the incorrect examples the entire iterable "data" would be
    stored in a single cell of the csv file.

    Args:
        file_name (str, or path-like object): path of the log file to use, does
            not need to include the file extension or previously exist.
        data: a sequence or unpacked iterable of data to be stored.

    Kwargs:
        init (bool, optional): Whether or not to open the log file in write
            mode ("True", for creating a new file) or append mode ("False" for
            adding additional data). Defaults to False.
    Example:
        cwd = Path().parent.resolve()
        file = cwd.joinpath('my_data')
        mydata = [3, 4, 5]
        moredata = {6, 7, 8}
        log_data(file, "column A", "column B", "column C", init=True)
        log_data(file, 1, 2, 3)
        log_data(file, *mydata)  # note use of generator
        log_data(file, *moredata)  # note use of generator
    """

    mode = 'w' if init else 'a'
    file_path = Path(file_path)
    file_path_ext = file_path.parent / f'{file_path.name}.csv'
    with open(file_path_ext, mode) as f:
        print(*data, sep=',', file=f)


def dump_data(directory, file_name, data):
    """
    dump_data(directory, file_name, data)

    Writes an iterable of iterables, such as a list of lists, row by row to a
    csv file. Useful for logging a large chunk of data at once after test or
    measurement.

    The arguements "directory" and "file_name" specify the path of the file to
    be created. The log file will be storted at directory/file_name.csv,
    file_name itself does not need to contain the file extension, it will
    automatically be added.

    The iterable "data" can contain an arbitrary number of elements which in
    turn can have arbitrary length and data type as long as it can be safely
    cast to a string. For example:

    data = [["column A", "column B", "column C"], [1, 2, 3], [4, 5, 6]]
    dump_data("some_directory", "my_data", data)

    Each element of data does not need to have the same length but it is
    recommended to make parsing the data after the fact easier.

    Args:
        directory (str, or path-like object): file directory where the log file
            is/will be stored.
        file_name (str): name of the log file to use, does not need to include
            the file extension.
        data: an iterable of iterables of data to be stored.

    Returns:
        NoneType
    """

    with open(Path(directory) / f'{file_name}.csv', 'w') as f:

        for item in data:
            print(*item, sep=',', file=f)

    return None


def dump_array_data(file_path: Path,
                    data: Iterable[Iterable[any]],
                    init: bool = False,
                    fill_value: Optional[str] = None) -> None:
    """
    dump_array_data(file_path, data, init=False, longest=False,
    fill_value=None)

    Writes a iterable of iterables to rows of a csv file by transposing them.
    Useful for logging data contained in multiple arrays, row by row after
    a test or measurement completes.
    if fill_value is not None, will pad with fill_value, default None

    example:


    If init=True a new file is created (or overwriten if the file already
    exists) and the iterable "data" is unpacked into the first row of the new
    document. If init = False then the existing file is opened and the iterable
    "data" is unpacked and appended to the end of the document. If init = False
    but the file does not already exist it will be created.

    The arguement "file_path" specifies the path of the file to be
    created/updated. The log file will be storted at file_path.csv
    , file_path itself does not need to contain the file extension, it will
    automatically be added.

    The iterable "data" can contain an arbitrary number of elements and each
    element can use an arbitrary data type as long as it can be safely cast to
    a string. The argument "data" SHOULD be passed as a PACKED structure,
    i.e. AS an iterable. For example:

        Incorrect:
            dump_array_data("my_data", 1, 2, 3, 4, 5)
            dump_array_data("my_data", *list_of_data)
            dump_array_data("my_data", *['a', 'b', 'c', 4, 5, 6])
            dump_array_data("my_data", *(1, 2, 3, 4, 5))
            dump_array_data("my_data", 'column 1', 'column 2', init=True)

        Correct:
            dump_array_data("my_data", [1, 2, 3, 4, 5])
            dump_array_data("my_data", (['a', 'b', 'c', 'd'], [1, 2, 3, 4, 5]),
                            init=True)

    Args:
        file_name (str, or path-like object): path of the log file to use, does
            not need to include the file extension or previously exist.
        data: an iterable of data to be stored.

    Kwargs:
        init (bool, optional): Whether or not to open the log file in write
            mode ("True", for creating a new file) or append mode ("False" for
            adding additional data). Defaults to False.
    Example:
        cwd = Path().parent.resolve()
        file = cwd.joinpath('my_data')
        list1 = ['a', 'b', 'c', 'd', 'e']
        list2 = [1, 2, 3, 4, 5, 6, 7, 8]
        list3 = [4, 5, 6, 7, 8, 9]
        args = (list1, list2, list3)
        dump_array_data(file, args, fill_value='')

        outputs as:
        a,1,4
        b,2,5
        c,3,6
        d,4,7
        e,5,8
        '',6,9
        '',7,''
        '',8,''

    """

    file_path = Path(file_path)
    file_path_ext = file_path.parent / f'{file_path.stem}.csv'

    if fill_value is not None:  # create generator
        rows = zip_longest(*data, fillvalue=fill_value)
    else:
        rows = zip(*data)

    with open(file_path_ext, 'w' if init else 'a') as f:
        print(*rows, sep=',', end='\n', file=f)


def create_test_log(base_dir, images=False, raw_data=False, **test_info):
    """
    create_test_log(base_dir, images=False, raw_data=False, **test_info)

    Creates a directory structure to be used for storing test data or
    measurements.

    The directory structure is created in the root directory
    specified by the arguement "base_dir". By default the name of the resulting
    directory will be "test_data_TIMESTAMP" where TIMESTAMP is record of when
    the directory was created in the format YYYYMMDDHHmmSS. To change the name
    of the directory structure pass an alternate name using the arguement
    "test_name". The timestamp is not optional and will always be added, this
    is included to prevent the accidently overwrite of data.

    Two additional sub-directories can be created within the directory
    structure by setting their boolean arguements "images" and "raw_data" to
    True. These arguements will create sub-folders with the same names within
    the directory structure. These directories are intended for storing images
    and raw data files respectively, in a more orgainized manner than in a flat
    directory.

    If any keyword arguements are passed they will be logged in a json file
    within the directory structure called "log_TIMESTAMP.json" This is intened
    to hold the configuration settings or any notes for a test or experiment
    that is to be run. In addition to any keyword arguements passed an addition
    key-value pair, ('run_time': TIMESTAMP) will be added to the json.

    Example:

    # The following code ...

        test_info = {'test_name': 'Transient_Measurements',
                     'v_in_setpoints': [40, 54, 60],
                     'i_out_setpoints': [100, 200, 300],
                     'measurement_delay': 2.0,
                     'dut': "SN0123456789"}
        create_test_log("example_dir", images=True, **test_info)

    # ... produces the directory structure below:

        example_dir |
                    |
                    ___ Transients_20210521095931 |
                                                  |
                                                  __ images
                                                  |
                                                  |
                                                  __ log_20210521095931.json

    Args:
        base_dir (str or Path-like object): root directory in which to create
            the directory structure.
        images (bool, optional): Whether or not to create a sub-directory
            called "images". Defaults to False.
        raw_data (bool, optional): Whether or not to create a sub-directory
            called "raw_data". Defaults to False.
    Kwargs:
        test_info: configuration information for a test or experiment. Can
            include an alternate name for the directory structure with the key
            "test_name". Will be logged to a json file

    Returns:
        Path-like object: The path to the newly created directory structure.
    """

    test_name = test_info.get('test_name', 'test_data')
    file_t_stamp = strftime(r"%Y%m%d%H%M%S")
    test_info['run_time'] = strftime(r"%Y/%m/%d %H:%M:%S")

    # make base directory for test log
    test_dir = Path(base_dir) / f'{test_name}_{file_t_stamp}'
    test_dir.mkdir(exist_ok=False)  # arg prevents accidently overwriting

    # optional sub-directories for images or raw data files
    if images:
        (test_dir / 'images').mkdir()
    if raw_data:
        (test_dir / 'raw_data').mkdir()

    # dump config dictionary to file if kwargs were passed
    if test_info:
        with open(test_dir / f'log_{file_t_stamp}.txt', 'w') as f:
            json.dump(test_info, f, indent=4,
                      check_circular=True,
                      allow_nan=True,
                      sort_keys=False)

    return test_dir  # return newly created directory


if __name__ == '__main__':
    pass
