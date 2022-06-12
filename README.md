# ofjustpy-react


## Webapp state management
modeling state and its transitions
### State variables
#### appstate
owned by session_manager
#### uistate
owned by ojr.WebPage 

### State transitions
#### ui_app_trmap
defines changes to appstate for uistate changes

#### app_actions_trmap 
defines actions to be taken on appstate changes

#### appctx_uiupdate_map
defines transformation to ui-elements for changes to appstate changes. 
Transformations include enable, hide/unhide/ update the text, etc. 

### The update pipeline
#### update_uistate
event_handler calls this to update uistate at spath with value

#### update_loop
this is invoked after following 
sequence of events:
- user performs actions
- event_handler is fired 
- uistate is updated   

The update_loop does following
- update appstate (using ui_app_trmap and changes to uistate)
- invoke actions based on appstate changes and app_actions_trmap (this can introduce further appstate)
- update ui-components bases on appstate changes and appctx_uiupdate_map



## Action annotations
### ojr.AppctxTrigger(<path>)
Annotate an action. Registers the action to be invoked when appstate has changed at `path` path. 
