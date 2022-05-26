import justpy as jp
import ofjustpy as oj
import ofjustpy_react as ojr
from addict import Dict
def build_components(session_manager):
    appstate = session_manager.appstate
    with session_manager.uictx("paratop") as paratopctx:
        _ictx = paratopctx
        @ojr.CfgLoopRunner
        def on_abtn_click(dbref, msg):
            return "/paratop/abtn", "show this text on textarea"

        oj.Button_("abtn", text="abtn", value="abtn").event_handle(oj.click, on_abtn_click)
        oj.Textarea_("atextarea", placeholder="this is text",
                     reactctx=[ojr.Ctx("/atextarea/value", ojr.isstr, ojr.UIOps.UPDATE_TEXT)]
                     )
    pass

import actions
ui_app_trmap_pairs  = [
    ("/paratop/abtn", "/atextarea/value", None)
    ]
@jp.SetRoute("/index.html")
def wp_index(request):
    session_manager = oj.get_session_manager(request.session_id)
    stubStore = session_manager.stubStore
    with oj.sessionctx(session_manager):
        build_components(session_manager)
        oj.Container_("tlc", cgens=[stubStore.paratop.abtn, stubStore.paratop.atextarea])
        wp = oj.WebPage_("wp_index",
                         page_type='quasar',
                         session_manager=session_manager,
                         WPtype=ojr.WebPage,
                         head_html_stmts=[],
                         cgens=[stubStore.tlc],
                         ui_app_trmap_iter = ui_app_trmap_pairs,
                         action_module=actions)()
    wp.session_manager = session_manager

    # wp.appstate = session_ctx.appstate

    return wp


request = Dict()
request.session_id = "abc123"

app=jp.app
jp.justpy(wp_index, start_server=False)
# wp = wp_index(request)
# session_manager = wp.session_manager
# stubStore = session_manager.stubStore
# msg = Dict()
# msg.page = wp

# stubStore.paratop.abtn.target.on_click(msg)
