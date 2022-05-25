from aenum import Enum, auto, IntEnum
import logging
import os
if os:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)


from aenum import Enum, auto, extend_enum

from functools import partial
import functools
import traceback
from typing import NamedTuple, Any

import justpy as jp




# def dupdate(addict, path, value):
#     # skip if path not already present
#     try:
#         dpop(addict, path)

#     except Exception as e:
#         raise e
#     dnew(addict, path, value)


class ReactTag_AppstateUpdate(Enum):
    """tags for actions that update the appstate
    """
    pass


class ReactTag_BackendAction(Enum):
    """tags for actions that run in background; may or may not update appstate. 
    check status of last executed operation -- either update noticeboard or advance to next processing step
    """
    #CHECK_OP_STATUS = partial(actions.CHECK_OP_STATUS)
    pass


def make_react(func, reacttag):
    extend_enum(reacttag, func.__name__, func)


class TaskStack:
    class Task(NamedTuple):
        tag: Any
        argdict: Any
        pass

    def __init__(self):
        self.tasks = []

    def addTask(self, tag, argdict):
        self.tasks.append(TaskStack.Task(tag, argdict))

    def taskIter(self):
        '''
        allows for tasks to be added during iteration
        '''

        idx = 0
        while True:
            if idx >= len(self.tasks):
                break

            if isinstance(self.tasks[idx], TaskStack.Task):
                yield self.tasks[idx]

            if isinstance(self.tasks[idx], TaskStack):
                yield from self.tasks[idx].taskIter()

            idx = idx + 1

    def addTaskSet(self, taskset):
        self.tasks.append(taskset)


class OpStatus(IntEnum):
    SUCCESS = auto()
    FAILED = auto()
    INPROGRESS = auto()
    pass


class ReactTag_UI(Enum):
    """tags for actions the update the frontend ui 
    """
    PageRedirect = auto()
    NoticeboardPost = auto()
    DockInfocard = auto()
    UndockInfocard = auto()

    pass


def run_looprunner(page: jp.WebPage, rts: TaskStack):
    """run model-view-update loop
    """
    update_appstate_and_ui = False
    for tag, arg in rts.taskIter():
        logger.info(f"current tasktag = {tag}")
        if isinstance(tag, ReactTag_AppstateUpdate):
            update_appstate_and_ui, newtaskset = tag.value(
                page.appstate, arg)
            if newtaskset:
                rts.addTaskSet(newtaskset)
        if isinstance(tag, ReactTag_BackendAction):
            update_appstate_and_ui, newtaskset = tag.value(
                page.appstate, arg)  # Not Very clean
            if newtaskset:
                rts.addTaskSet(newtaskset)
        if isinstance(tag, ReactTag_UI):
            page.react_ui(tag, arg)

    if update_appstate_and_ui:
        print("looprunner: calling update_appstate_and_ui")
        page.update_appstate_and_ui()


def CfgLoopRunner(func):
    '''run react-update ui loop for event hangles

    '''
    @functools.wraps(func)
    def signal_wrapper(*args, **kwargs):
        '''
        wrap ui_action_signal to follow
        model_update_view cycle
        '''
        #func(*args, **kwargs)
        #run_looprunner(page, rts)

        dbref = args[0]
        spath = dbref.stub.spath
        msg = args[1]

        wp = msg.page

        #analytics_dashboard uses dummy function for event handler
        sspath, svalue = func(*args, **kwargs)
        # if not value: 
        #     value = msg.value
        logger.debug(f"=====> begin cfgLoopRunner: react-to-event: {sspath} {svalue}")
        #
        wp.update_uistate(sspath, svalue)
        wp.update_loop()
        logger.debug("=====> end cfgLoopRunner")

        pass
        # func(*args, **kwargs)
    return signal_wrapper


def LoopRunner(func):
    '''run react-update ui loop for event hangles

    '''
    @functools.wraps(func)
    def signal_wrapper(*args, **kwargs):
        '''
        wrap ui_action_signal to follow
        model_update_view cycle
        '''
        page, rts = func(*args, **kwargs)
        run_looprunner(page, rts)
        pass
        # func(*args, **kwargs)
    return signal_wrapper


def UpdateAppStateAndUI(func):
    '''Tells the  loop runner to 
    update appstate and UI based on changes
    to cfg_appstate and cfg_ui.
    '''
    @functools.wraps(func)
    def signal_wrapper(*args, **kwargs):
        '''
        wrap ui_action_signal to follow
        model_update_view cycle
        '''
        rts = func(*args, **kwargs)
        return (True, rts)
        pass
        # func(*args, **kwargs)
    return signal_wrapper
