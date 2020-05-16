import sys
import traceback
import numpy as np
import os
import functools
import logging
from logging.handlers import RotatingFileHandler

from utils.date_time_utility import get_date
from utils.dictionary_set import handle_dictionary


def extract_function_name():
    """Extracts failing function name from Traceback
    by Alex Martelli
    http://stackoverflow.com/questions/2380073/\
    how-to-identify-what-function-call-raise-an-exception-in-python
    """
    tb = sys.exc_info()[-1]
    stk = traceback.extract_tb(tb, 1)
    function_name = stk[0][3]
    return function_name


def create_logger(folder_path, exp_name):
    logger = logging.getLogger("PyTrainer-log")
    logger.setLevel(logging.DEBUG)
    log_path = os.path.join(folder_path, exp_name + ".log")

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    log_format = " \033[1;37m>>\033[0m \033[93m[%(asctime)s][%(name)s][%(levelname)s] \033[0;37m-\033[0m %(message)s"
    formatter = logging.Formatter(log_format)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fl = logging.FileHandler(log_path)
    fl.setLevel(logging.INFO)
    fl_format = logging.Formatter("%(asctime)s %(name)s : %(levelname)s : %(message)s")
    fl.setFormatter(fl_format)
    logger.addHandler(fl)

    rfl = RotatingFileHandler(
        os.path.join(folder_path, exp_name + "_extensive.log"), maxBytes=1024
    )
    rfl.setLevel(logging.DEBUG)
    rfl_format = logging.Formatter("%(asctime)s %(name)s : %(levelname)s : %(message)s")
    rfl.setFormatter(rfl_format)
    logger.addHandler(rfl)

    logger.info("Experiment {} conducted on : {}".format(exp_name, get_date()))

    sys.stdout.writelines = logger.info


def remove_nd_array(*args, **kwargs):
    new_arg = list()
    new_kwargs = dict()
    for individual_argument in args:
        if type(individual_argument) == np.ndarray:
            new_arg.append("nd array")
        else:
            new_arg.append(individual_argument)

    for key, value in kwargs.items():
        if type(value) == np.ndarray:
            new_kwargs = handle_dictionary(new_kwargs, key, "nd array")
        else:
            new_kwargs = handle_dictionary(new_kwargs, key, value)
    return tuple(new_arg), new_kwargs


def get_function_name(fn):
    class_name = vars(sys.modules[fn.__module__])[
        fn.__qualname__.split(".")[0]
    ].__name__
    fn_name = fn.__name__
    if class_name == fn_name:
        return fn_name
    else:
        return class_name + "-->" + fn_name


class PtLogger(object):
    def __init__(self, debug=False):
        self.logger = logging.getLogger("PyTrainer-log")
        self.debug = debug

    def __call__(self, fn):
        @functools.wraps(fn)
        def log_decorated(*args, **kwargs):
            try:
                new_args, new_kwargs = remove_nd_array(*args, **kwargs)
                if self.debug:
                    self.logger.debug(
                        "{0} - {1} - {2} - {3}".format(
                            "Input to", get_function_name(fn), new_args, new_kwargs
                        )
                    )
                else:
                    self.logger.info("{}".format(get_function_name(fn)).upper())
                result = fn(*args, **kwargs)
                if self.debug:
                    new_args, _ = (
                        remove_nd_array(*result)
                        if type(result) == tuple
                        else remove_nd_array(*[result])
                    )
                    self.logger.debug(
                        "{0} - {1} - {2}".format(
                            "Output of", get_function_name(fn), new_args
                        )
                    )
                return result
            except KeyboardInterrupt as ex:
                msg = "Function {function_name} raised {exception_class} ({exception_docstring}): {exception_message}".format(
                    function_name=extract_function_name(),
                    exception_class=ex.__class__,
                    exception_docstring=ex.__doc__,
                    exception_message=ex,
                )
                self.logger.debug("{0} - {1} - {2}".format(fn.__name__, args, kwargs))
                self.logger.exception("Exception {0}".format(msg))
                raise ex
            except Exception as ex:
                msg = "Function {function_name} raised {exception_class} ({exception_docstring}): {exception_message}".format(
                    function_name=extract_function_name(),
                    exception_class=ex.__class__,
                    exception_docstring=ex.__doc__,
                    exception_message=ex,
                )
                self.logger.debug("{0} - {1} - {2}".format(fn.__name__, args, kwargs))
                self.logger.exception("Exception {0}".format(msg))
                raise ex

        return log_decorated
