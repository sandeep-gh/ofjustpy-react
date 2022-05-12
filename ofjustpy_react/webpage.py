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




import justpy as jp
from addict import Dict
import ofjustpy as oj

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
    path: Any
    condition: Any
    uiop: Any
    
class UIOps(Enum):
    DISABLE = auto()
    ENABLE = auto()
    UPDATE_NOTICEBOARD = auto()
    APPEND_CLASSES = auto()
    
def components_in_appstate_changectx(kpath, val,  app_ui_trmap):
    """
    which components have registered for the change.
    returns components path in cfgCM
    """

    for path, am in oj.dictWalker(app_ui_trmap):
        #am: attrmeta
        # TODO: this check should become more sophisticated
        # moving to a sophisticated check
        for ctx in am.appstate_context:
            if kpath == ctx.path:
                # candidate_ctx[1] is either a string value or a lambda
                if ctx.condition(val):
                    yield path, ctx.uiop

                    
def uiops_for_appstate_change_ctx_kpath(kpath, val, app_ui_trmap, appstate):
    """
    update cfgCM in response to  changes in appstate at kpath
    """
    ctx = (kpath, val)

    logger.debug(f"evaluation ctx: {ctx}")
    paths_in_context = [
        _ for _ in components_in_appstate_changectx(kpath, val,  app_ui_trmap)]
    for path, uiop in paths_in_context:
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
        logger.info(
            f"changing ui for {path} with uiop {uiop}")

        yield path, uiop
        pass


def uiops_for_appstate_change_ctx(appstate, app_ui_trmap, new_inactive_kpaths=[]):
    """
    a change on frontend/browser is recorded in cfg_ui and in appstate.
    update cfg_CM based on dependency
    """
    for kpath in appstate.get_changed_history():
        new_val = dget(appstate, kpath)
        logger.debug(
            f"{kpath} has changed in appstate to  new_value={new_val}")
        yield from uiops_for_appstate_change_ctx_kpath(
            kpath, new_val, app_ui_trmap, appstate)

    for kpath in new_inactive_kpaths:
        logger.debug("inactive paths are not implemented yet")
        pass

    logger.debug("done update ui for appstate cha...")


#initialize ui_app_trmap from app_ui_trmap    
def refresh_uistate(app_ui_trmap, uistate):
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
    def __init__(self, ui_app_trmap_iter=None, app_ui_trmap_iter=None,  app_actions_trmap_iter=None, session_manager=None, **kwargs):
        """
        cfg_CM: config component meta
        uiState_dependencyGraph_iter: list for each dbref behaves in various Ctx. 
        actions_dependencyGraph_iter: actions to execute in various context
        """
        super().__init__(**kwargs)
        self.session_manager = session_manager
        self.appstate = session_manager.appstate
        self.stubStore = session_manager.stubStore
        #stores the value/state of active/input ui components
        self.uistate = Dict(track_changes=True)
        #mapping appstate change context to ui ops per ui component
        self.app_ui_trmap = Dict(track_changes=True)
        #mapping from ui state change to appstate changes
        self.ui_app_trmap = Dict(track_changes=True)
        #mapping from appstate changes to backend/appstate actions
        self.app_actions_trmap = Dict(track_changes=True)        
        
        for spath, attrmeta in app_ui_trmap_iter:
            oj.dnew(self.app_ui_trmap, spath, attrmeta)
        # list of 2item tuples: spath, apppath, transformation
        for spath, appchangectx in ui_app_trmap_iter:
            oj.dnew(self.ui_app_trmap, spath, appchangectx)

        for spath, actions_directives in app_actions_trmap_iter:
            oj.dnew(self.app_actions_trmap, spath, actions_directives)

        #set all paths from app_ui_tr to uistate
        refresh_uistate(self.app_ui_trmap, self.uistate)
        self.ui_app_trmap.clear_changed_history()
        self.uistate.clear_changed_history()
        self.app_ui_trmap.clear_changed_history()
        logger.debug("----app_ui_trmap----")
        logger.debug(self.app_ui_trmap)

        logger.debug("----ui_app_trmap----")
        logger.debug(self.ui_app_trmap)

        logger.debug("----appstate----")
        logger.debug(self.appstate)

        logger.debug("----uistate----")
        logger.debug(self.uistate)
        

    def update_uistate(self, spath, value):
        """
        set value of cfg_ui at spath value
        """
        old_val = oj.dget(self.uistate, spath)
        logger.debug(
             f"react: update uistate: key={spath} from {old_val} to new value {value}")
        oj.dupdate(self.uistate, spath, value)

    def update_loop(self):
        """
        user has changed the state of ui input component.
        this has led to change in values in  uistate.

        in this function we loop:
        1. update appstate for uistate changes via ui_app_trmap

        """

        # update appstate from cfg_ui
        for _ in self.uistate.get_changed_history():
            uival = oj.dget(self.uistate, _)
            app_path = None
            print(f"{self.ui_app_trmap['twreference']}")
            
            if oj.dsearch(self.ui_app_trmap, _):
                app_path, value_tranformer = oj.dget(self.ui_app_trmap, _)
                if value_tranformer:
                    appval = value_tranformer[uival]
                else:
                    appval = uival
                    
            else:
                try:
                    res = oj.dget(self.appstate, _)
                    # as long as path exists update appstate
                    if res == None or res:
                        logger.debug(f"react-to-ui-change: update appstate for path {_}")
                        app_path = _
                        appval = uival
                        
                except KeyError as e:
                    print(f"path {_} not in appstate: will not change appstate")
                except Exception as e:
                    print("here {e}")
                    raise e
            if app_path:
                oj.dupdate(self.appstate, app_path,  appval)

        self.appstate.clear_changed_history()
        # perform actions for updated appstate
        
        appstate_changeset = [_ for _ in self.appstate.get_changed_history()]
        logger.debug(f"post uistate update:  appstate changes {appstate_changeset}")
        for kpath in appstate_changeset:
            kval = oj.dget(self.appstate, kpath)
            if(kpath, kval) in self.app_actions_trmap:
                logger.debug(f"TODO: Exec actions for {kpath}, {kval}")
                #exec_actions(self.cfg_actions[(kpath,kval)], self.appstate)
                print("status post op = ", self.appstate.op_status)
            pass

        # actions and cfg_ui have updated appstate  ==> try to update cfg_CM and the ui
        for kpath, uiop in uiops_for_appstate_change_ctx(self.appstate, self.app_ui_trmap):
            match uiop:
                case UIOps.ENABLE:
                    target_dbref = dget(stubStore, kpath).target
                    target_dbref.remove_class("disabled")
                    pass
                case UIOps.DISABLE:
                    pass
                case UIOps.UPDATE_NOTICEBOARD:
                    print("notice board not yet implemented")

        self.appstate.clear_changed_history()
        pass

    
