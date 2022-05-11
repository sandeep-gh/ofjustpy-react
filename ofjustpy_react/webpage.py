"""
attrmeta is a graball module for all metadata about chartjs attributes
"""
import logging
from typing import Any, NamedTuple
import os
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
    is_active: Any
    ui_context: Any
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

    
def components_in_appstate_changectx(kpath, val,  cfg_CM):
    """
    which components have registered for the change.
    returns components path in cfgCM
    """

    for path, am in dictWalker(cfg_CM):
        #am: attrmeta
        # TODO: this check should become more sophisticated
        # moving to a sophisticated check
        for ctx in am.appstate_context:
            if kpath == ctx.path:
                # candidate_ctx[1] is either a string value or a lambda
                if ctx.condition(val):
                    yield path, ctx.uiop

                    
def update_cfg_CM_kpath_for_appstate_changes(kpath, val, cfg_CM, appstate):
    """
    update cfgCM in response to  changes in appstate at kpath
    """
    ctx = (kpath, val)

    logger.debug(f"evaluation ctx: {ctx}")
    paths_in_context = [
        _ for _ in components_in_appstate_changectx(kpath, val,  cfg_CM)]
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


def update_cfg_CM_for_appstate_changes(appstate,  cfg_CM, new_inactive_kpaths=[]):
    """
    a change on frontend/browser is recorded in cfg_ui and in appstate.
    update cfg_CM based on dependency
    """
    for kpath in appstate.get_changed_history():
        new_val = dget(appstate, kpath)
        logger.debug(
            f"{kpath} has changed in appstate to  new_value={new_val}")
        yield from update_cfg_CM_kpath_for_appstate_changes(
            kpath, new_val, cfg_CM, appstate)

    for kpath in new_inactive_kpaths:
        logger.debug("inactive paths are not implemented yet")
        pass

    logger.debug("done update_cfgattrmeta...")

    
def update_cfg_ui(cfg_CM, cfg_ui, path_filter):
    """
    this can be made generic for sure. 
    path_filter: condition to avoid changed path

    """
    logger.debug("=========== start update_cfg_ui  ===============")
    # remove everything thats changed and put it
    # back in only the active ones: this enables deletion
    inactive_kpaths = set()
    for kpath in cfg_CM.get_changed_history():
        logger.debug(f"path {kpath} changed in cfgattrmeta")
        try:
            # logger.debug("what bakwas")
            # opts = jsbeautifier.default_options()
            # logger.debug(jsbeautifier.beautify(json.dumps(cjscfg), opts))
            oj.dpop(cfg_ui, kpath)
            inactive_kpaths.add(kpath)
        except oj.PathNotFound as e:
            logger.info(f"skipping: {kpath} not found in cjscfg {e}")
            pass  # skip if path is not in chartcfg
        pass
    for kpath in filter(path_filter,
                        cfg_CM.get_changed_history()):

        #evalue = get_defaultVal(dget(cfg_CM, kpath))
        evalue = oj.dget(cfg_CM, kpath).default
        oj.dnew(cfg_ui, kpath, evalue)
        if kpath in inactive_kpaths:
            inactive_kpaths.remove(kpath)
        logger.debug(f"path {kpath} updated with {evalue} in cjscfg")

    # cfgattrmeta.clear_changed_history()
    if inactive_kpaths:
        logger.debug(f"paths that became inactive: {inactive_kpaths}")
    logger.debug("=========== done update_chartCfg  ===============")
    return inactive_kpaths


class WebPage(jp.WebPage):
    def __init__(self, uiState_dependencyGraph_iter, actions_dependencyGraph_iter, session_manager, **kwargs):
        """
        cfg_CM: config component meta
        uiState_dependencyGraph_iter: list for each dbref behaves in various Ctx. 
        actions_dependencyGraph_iter: actions to execute in various context
        """
        super().__init__(**kwargs)
        self.session_manager = session_manager
        self.appstate = session_manager.appstate
        self.stubStore = session_manager.stubStore
        self.cfg_CM = Dict(track_changes=True)
        self.cfg_ui = Dict(track_changes=True)
        self.cfg_actions = Dict(track_changes=True)        
        
        for spath, attrmeta in uiState_dependencyGraph_iter:
            oj.dnew(self.cfg_CM, spath, attrmeta)
        for spath, actions_directives in actions_dependencyGraph_iter:
            oj.dnew(self.cfg_actions, spath, actions_directives)
            
        update_cfg_ui(self.cfg_CM, self.cfg_ui, lambda kpath, cfg_CM=self.cfg_CM: oj.dget(cfg_CM, kpath).is_active)


        self.cfg_CM.clear_changed_history()
        self.cfg_ui.clear_changed_history()
        logger.debug("---------init cfg_ui----------")
        logger.debug(self.cfg_ui)

        
    def cfg_ui_setval(self, spath, value):
        """
        set value of cfg_ui at spath value
        """
        old_val = oj.dget(self.cfg_ui, spath)
        logger.debug(
             f"react: update cfg_ui: key={spath} from {old_val} to new value {value}")
        oj.dupdate(self.cfg_ui, spath, value)

    def cfg_update_loop(self):
        """
        user has changed the state of input component.
        this has led to change in values in  cfg_ui.
        in this function we update ui on update to cfg_ui
        1. update cfg_mode based on new context in cfg_ui
        2.
        """

        # update appstate from cfg_ui
        for _ in cfg_ui.get_changed_history():
            try:
                res = oj.dget(self.appstate, _)
                # as long as path exists update appstate
                if res == None or res:
                    logger.debug(f"react-cfguichange: update appstate for path {_}")
                    oj.dupdate(appstate, _,  oj.dget(self.cfg_ui, _))
            except KeyError as e:
                print(f"path {_} not in appstate")
            except Exception as e:
                print("here {e}")
                raise e

        self.cfg_ui.clear_changed_history()
        # perform actions for updated appstate
        
        appstate_changeset = [_ for _ in self.appstate.get_changed_history()]
        logger.debug(f"post cfgui update  appstate changes {appstate_changeset}")
        for kpath in appstate_changeset:
            kval = oj.dget(self.appstate, kpath)
            if(kpath, kval) in self.cfg_actions:
                logger.debug(f"TODO: Exec actions for {kpath}, {kval}")
                exec_actions(self.cfg_actions[(kpath,kval)], self.appstate)
                print("status post op = ", self.appstate.op_status)
            pass

        # actions and cfg_ui have updated appstate  ==> try to update cfg_CM and the ui
        for kpath, uiop in update_cfg_CM_for_appstate_changes(appstate, cfg_CM):
            match uiop:
                case UIOps.ENABLE:
                    target_dbref = dget(stubStore, kpath).target
                    target_dbref.remove_class("disabled")
                    pass
                case UIOps.DISABLE:
                    pass
                case UIOps.UPDATE_NOTICEBOARD:
                    print("notice board not yet implemented")

        appstate.clear_changed_history()
        pass

    
