"""
attrmeta is a graball module for all metadata about chartjs attributes
"""
import logging
from typing import Any, NamedTuple
import os
from aenum import Enum, auto
if logging:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)



import inspect
import justpy as jp
from addict import Dict
import ofjustpy as oj

def is_mod_function(mod, func):
    return inspect.isfunction(func) and inspect.getmodule(func) == mod


def list_functions(mod):
    return filter(lambda func, mod=mod: is_mod_function(mod, func),
                  mod.__dict__.values()
                  )


class OpaqueDict(NamedTuple):
    """
    Hide dict from addict/changed history
    """
    value: Dict
    pass


class UIAppCtx(NamedTuple):
    uipath: Any
    apppath: Any
    valueop: Any
    
class AttrMeta(NamedTuple):
    """
    metadata about ui component
    """
    default: Any
    appstate_context: Any

# class AttrMetaUIAppstate(NamedTuple):
#     ui_context:Any
# _cfg = cfg_UI_appstate_transition_matrix = Dict(track_changes=True)
# _cfg.dbsession.id  = AttrMetaUIAppstate("/dbsess

def eq_op(val):
    return lambda x, val=val: x == val


def isstr(val):
    return isinstance(val, str)



class Ctx(NamedTuple):
    apppath: Any
    condition: Any
    uiop: Any
    
class UIOps(Enum):
    DISABLE = auto()
    ENABLE = auto()
    UPDATE_NOTICEBOARD = auto()
    APPEND_CLASSES = auto()
    #update text attribute of a class
    UPDATE_TEXT = auto()

    #redirect to new page
    REDIRECT = auto()

    # call deck.bring_to_front
    DECK_SHUFFLE = auto()

    DEBUG = auto()
    
    UPDATE_CHART = auto()
    
def components_in_appstate_changectx(apppath, val,  appctx_uiupdate_map):
    """
    which components have registered for the change.
    returns components path in cfgCM
    """

    try:
        spath, appchangectx = oj.dget(appctx_uiupdate_map,  apppath)
        if appchangectx.condition(val):
            yield spath, appchangectx
    except Exception as e:
        logger.debug(f"{apppath} not in appctx_uiupdate_map {e}")

                    
def uiops_for_appstate_change_ctx_kpath(kpath, val, appctx_uiupdate_map):
    """
    update cfgCM in response to  changes in appstate at kpath
    """

    #logger.debug(f"evaluation ctx: apppath:{kpath} val={val}")
    affected_uis = [
        _ for _ in components_in_appstate_changectx(kpath, val,  appctx_uiupdate_map)]
    for spath, appchangectx in affected_uis:
        # TODO: we should change something for sure.
        # the bojective is to update the ui with newly added data model
        # dget(stubStore, path).target.update(val)
        # print(f"Que {path} {kpath} {val} {cm}")
        # match ctx.uiop:
        #     case UIOps.ENABLE:
        #         #dset(cfg_CM, path, "enabled")
        #         #am.is_enabled = True
        #     case UIOps.DISABLE:
        #         #dset(cfg_ui, path, "disabled")
        # logger.info(
        #     f"changing ui for {spath} with uiop {appchangectx.uiop}")

        yield spath, val, appchangectx.uiop




#def uiops_for_appstate_change_ctx(appstate, appctx_uiupdate_map, new_inactive_kpaths=[], path_guards = None):
def uiops_for_appstate_change_ctx(appstate_all_changed_paths,
                                  appctx_uiupdate_map,
                                  appstate,
                                  new_inactive_kpaths=[],
                                  path_guards = None):
    
    """
    a change on frontend/browser is recorded in cfg_ui and in appstate.
    update cfg_CM based on dependency
    """
    #all_changed_paths = [_ for _ in appstate.get_changed_history(path_guards = path_guards)]
    #logger.debug (f"appstate:all_changed_paths {all_changed_paths}")
    for kpath in appstate_all_changed_paths:
        new_val = oj.dget(appstate, kpath)
        # logger.debug(
        #     f"{kpath} has changed in appstate to  new_value={new_val}")
        yield from uiops_for_appstate_change_ctx_kpath(
            kpath, new_val, appctx_uiupdate_map)

    for kpath in new_inactive_kpaths:
        logger.debug("inactive paths are not implemented yet")
        pass

    #logger.debug("done update ui for appstate cha...")


#initialize ui_app_trmap from app_ui_trmap    
def refresh_uistate(app_ui_trmap, uistate, stubStore):
    """
    this can be made generic for sure. 
    path_filter: condition to avoid changed path

    """
    logger.debug("=========== start update_cfg_ui  ===============")
    # remove everything thats changed and put it
    # back in only the active ones: this enables deletion
    inactive_kpaths = set()
    for kpath in app_ui_trmap.get_changed_history():
        logger.debug(f"path {kpath} changed in cfgattrmeta")
        try:
            # logger.debug("what bakwas")
            # opts = jsbeautifier.default_options()
            # logger.debug(jsbeautifier.beautify(json.dumps(cjscfg), opts))
            oj.dpop(uistate, kpath)
            inactive_kpaths.add(kpath)
        except oj.PathNotFound as e:
            logger.info(f"skipping: {kpath} not found in uistate {e}")
            pass  # skip if path is not in chartcfg
        pass
    for kpath in app_ui_trmap.get_changed_history():

        #evalue = get_defaultVal(dget(cfg_CM, kpath))
        evalue = oj.dget(app_ui_trmap, kpath).default
        oj.dnew(uistate, kpath, evalue)
        if kpath in inactive_kpaths:
            inactive_kpaths.remove(kpath)
        logger.debug(f"path {kpath} updated with {evalue} in uistate")

    # cfgattrmeta.clear_changed_history()
    if inactive_kpaths:
        logger.debug(f"paths that became inactive: {inactive_kpaths}")
    logger.debug("=========== done refresh_uistate  ===============")
    return inactive_kpaths


class WebPage(jp.WebPage):
    def __init__(self, ui_app_trmap_iter=[],  session_manager=None, path_guards = None, enable_quasar=False, action_module=None,  **kwargs):
        """
        cfg_CM: config component meta
        uiState_dependencyGraph_iter: list for each dbref behaves in various Ctx. 
        actions_dependencyGraph_iter: actions to execute in various context
        action_module: module with all the actions/functions that defines reaction. 
        """

        super().__init__(**kwargs)
        if enable_quasar:
            self.template_file = 'quasar.html'
            self.quasar = True

        self.session_manager = session_manager
        self.appstate = session_manager.appstate
        self.stubStore = session_manager.stubStore
        self.path_guards = path_guards

        # ============ build appctx to action trigger map ============
        self.app_actions_trmap = Dict(track_changes=True)
        if action_module:
            for afunc in list_functions(action_module):
                if inspect.getdoc(afunc) is None:
                    continue
                doctoks = inspect.getdoc(afunc).split()
                if doctoks:
                    if 'appctx' in doctoks[0]:
                        spath = doctoks[0].split(":")[1]
                        oj.dnew(self.app_actions_trmap, spath, [afunc])


        # build appctx to ui update map
        self.appctx_uiupdate_map = Dict(track_changes=True)
        for spath, stub in oj.dictWalker(self.stubStore):

            if 'reactctx' in stub.kwargs:
                for appchangectx in stub.kwargs.get('reactctx'):#TODO: what if apppath already exists
                    oj.dnew(self.appctx_uiupdate_map, appchangectx.apppath, (spath, appchangectx))
                  
        #stores the value/state of active/input ui components
        self.uistate = Dict(track_changes=True)

        #mapping from uistate changes to appstate 
        self.ui_app_trmap = Dict(track_changes=True)
        for uipath, apppath, valop  in ui_app_trmap_iter:
            oj.dnew(self.ui_app_trmap, uipath, (apppath, valop))

        #refresh_uistate(self.appctx_uiupdate_map, self.uistate, self.stubStore)
        self.ui_app_trmap.clear_changed_history()
        self.uistate.clear_changed_history()
        self.appctx_uiupdate_map.clear_changed_history()
        logger.debug("----appctx_uiupdate_map----")
        logger.debug(self.appctx_uiupdate_map)
        logger.debug("----ui_app_trmap----")
        logger.debug(self.ui_app_trmap)
        logger.debug("----app_actions_trmap----")
        logger.debug(self.app_actions_trmap)

        logger.debug("----appstate----")
        logger.debug(self.appstate)
        logger.debug("----uistate----")
        logger.debug(self.uistate)
        

    def update_uistate(self, spath, value):
        """
        set value of cfg_ui at spath value
        """
        try:
            old_val = oj.dget(self.uistate, spath)
            logger.debug(
                f"Phase 1: update-uistate:   update ui: key/path={spath};  old_val = {old_val};  new_value= {value}")
            oj.dupdate(self.uistate, spath, value)
        except KeyError as e:
            oj.dnew(self.uistate, spath, value)
            logger.debug(
                f"Phase 1:update_uistate:add-new-path-and-value: update key={spath}, value={value}")
        


    def build_list(self):
        return super().build_list()
    
    def update_loop(self):
        """
        user has changed the state of ui input component.
        this has led to change in values in  uistate.

        in this function we loop:
        1. update appstate for uistate changes via ui_app_trmap
        2. perform actions
        3. update ui

        """

        logger.debug("*********** Begin Phase 2: update appstate (from ui)")
        
        for _ in self.uistate.get_changed_history():
            uival = oj.dget(self.uistate, _)
            logger.debug(f"             changed ui path: {_}")
            app_path = None
            appval = None
            if oj.dsearch(self.ui_app_trmap, _):
                app_path, value_tranformer = oj.dget(self.ui_app_trmap, _)
                appval = uival
                if value_tranformer:
                    appval = value_tranformer(uival)
            elif oj.dsearch(self.appstate, _):
                app_path = _
                appval = uival


            if app_path:
                if oj.dsearch(self.appstate, _):
                    logger.debug(f"            matching app path:update: {app_path} with appval={appval}")
                    oj.dupdate(self.appstate, app_path,  appval)
                else:
                    logger.debug(f"            matching app path:new: {app_path} with appval={appval}")
                    oj.dnew(self.appstate, app_path,  appval)
                
            else:
                logger.debug(f"path {_} does not exists in appstate or in ui_app_trmap: skipping")
                
 
        # perform actions for updated appstate
        self.uistate.clear_changed_history()
        logger.debug("*********** End Phase 2: update appstate")

        for bigloop in range(3):
            logger.debug(f"*********** Begin Phase 3: trigger actions; bigloop:{bigloop}")

            appstate_all_changed_paths = [_ for _ in self.appstate.get_changed_history(path_guards = self.path_guards)]
            self.appstate.clear_changed_history()
            #logger.debug(f"post ui-->app state update:  appstate changes {appstate_changeset}")
            for kpath in appstate_all_changed_paths :
                logger.debug (f"            visiting appstate path: {kpath}")
                kval = oj.dget(self.appstate, kpath)
                if oj.dsearch(self.app_actions_trmap, kpath):

                    #TODO: handle series of actions
                    action_fns = oj.dget(self.app_actions_trmap, kpath)
                    logger.debug(f"       actions invoked: {action_fns}" )
                    for action_fn in action_fns:
                        action_fn(self.appstate, kval)
                pass

            # actions and cfg_ui have updated appstate  ==> try to update cfg_CM and the ui
            logger.debug("*********** End Phase 3: trigger actions")

            logger.debug("*********** Begin Phase 4: Update UI")
            for spath,  kval, uiop in uiops_for_appstate_change_ctx(appstate_all_changed_paths, self.appctx_uiupdate_map, self.appstate):
                logger.debug(f" visiting app path: {spath} uiop:{uiop} val:{kval}")
                target_dbref = oj.dget(self.stubStore, spath).target
                match uiop:
                    case UIOps.ENABLE:
                        target_dbref.remove_class("disabled")
                        pass
                    case UIOps.DISABLE:
                        pass
                    case UIOps.UPDATE_NOTICEBOARD:
                        print("notice board not yet implemented")
                    case UIOps.DECK_SHUFFLE:
                        target_dbref.bring_to_front(kval)
                    case UIOps.UPDATE_CHART:
                        logger.debug("Update chart called with stub path/key: {spath} {kval}")
                        target_dbref.update_chart(kval[0], kval[1])
                        #target_dbref.update_chart(kval)                     
                    case UIOps.UPDATE_TEXT:
                        logger.debug("in uiops.update_text: ")
                        #TODO: when it is text vs. placeholder
                        match target_dbref.html_tag:
                            case 'input':
                                 target_dbref.placeholder = kval
                            case 'span':
                                 target_dbref.text = kval
                            case _:
                                 print("unkown how to update text for : ", target_dbref.html_tag)
                    case UIOps.REDIRECT:
                        logger.debug(f"in uiops.redirect for : {target_dbref.stub.key} {kval}" )
                        target_dbref.redirect = kval
                        #TODO: when it is text vs. placeholder
                        #target_dbref.placeholder = kval
                    case UIOps.DEBUG:
                        logger.debug(f"I am at debug with kval  = {kval}")
            #self.appstate.clear_changed_history()
            #self.uistate.clear_changed_history()
            logger.debug("*********** End Phase 4: Update UI")

        
        pass

    
