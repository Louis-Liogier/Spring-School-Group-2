# %%
import bw2io as bi
import bw2data as bd
import bw2calc as bc
from bw_graph_tools import NewNodeEachVisitGraphTraversal
import pandas as pd
import panel as pn

#https://panel.holoviz.org/developer_guide/extensions.html#extension-plugins
pn.extension()

# https://panel.holoviz.org/reference/widgets/Tabulator.html
pn.extension('tabulator')

# BRIGHTAY SETUP ################################################################

def check_for_useeio_brightway_project():
    if 'USEEIO-1.1' not in bd.projects:
        bi.install_project(project_key="USEEIO-1.1", overwrite_existing=True)
    bd.projects.set_current(name='USEEIO-1.1')
    useeio = bd.Database("USEEIO-1.1")
    return useeio

useeio = check_for_useeio_brightway_project()

list_of_useeio_products=[
    node['name'] for node in useeio
    if 'product' in node['type']
]

# PANEL SETUP ###################################################################

search_string =''
lca_score = 0
df_activities = pd.DataFrame()

# https://panel.holoviz.org/reference/widgets/AutocompleteInput.html
widget_autocomplete_input_activity = pn.widgets.AutocompleteInput(
    name='Autocomplete Product Selection',
    options=list_of_useeio_products,
    case_sensitive=False,
    search_strategy='includes',
    placeholder='Write something her...'
)

# https://panel.holoviz.org/reference/widgets/Button.html
widget_button_activity = pn.widgets.Button(
    name='Click me to calculate LCA score!',
    button_type='primary'
)

# https://panel.holoviz.org/reference/widgets/Button.html
widget_button_tabulator = pn.widgets.Button(
    name='Click me to perform temporalization!',
    button_type='primary'
)

# https://panel.holoviz.org/reference/widgets/StaticText.html
widget_static_text = pn.widgets.StaticText(
    name='Selected Database Activity',
    value="Nothing yet"
)

# this needs to be updated
tabulator_editors = {
    'int': None,
    'float': {'type': 'number', 'max': 10, 'step': 0.1},
    'bool': {'type': 'tickCross', 'tristate': True, 'indeterminateValue': None},
    'str': {'type': 'list', 'valuesLookup': True},
    'date': 'date',
    'datetime': 'datetime'
}

# https://panel.holoviz.org/reference/widgets/Tabulator.html
widget_tabulator = pn.widgets.Tabulator(
    df_activities,
)

pane_bokeh = pn.pane.Bokeh(
    create_bokeh_figure(x,y),
    theme="dark_minimal"
)


# CALCULATION FUNCTIONS ######################################################


def select_database_activity(search_string):
    # https://docs.brightway.dev/en/latest/content/gettingstarted/objects.html#object-selection
    selected_activity = [
        node for node in useeio
        if search_string.lower() == node['name'].lower()
        and 'product' in node['type']
    ][0] # this just selects the first element in the list
    return selected_activity


def perform_lca_and_path_analysis(
    selected_activity,
) -> pd.DataFrame:
    # https://docs.brightway.dev/en/latest/content/gettingstarted/lca.html#calculate-one-lcia-result
    lca = bc.LCA(
        demand={selected_activity: 1},
        method=('Impact Potential', 'GCC') # globaJl climate change
    )
    lca.lci()
    lca.lcia()
    lca_score = round(lca.score,2)

    # https://docs.brightway.dev/projects/graphtools/en/latest/content/api/bw_graph_tools/graph_traversal/index.html#bw_graph_tools.graph_traversal.NewNodeEachVisitGraphTraversal
    graph_traversal_result = NewNodeEachVisitGraphTraversal.calculate(lca, cutoff=0.01)

    return lca_score, pd.DataFrame.from_dict(graph_traversal_result['nodes'], orient='index')


# PLOTTING FUNCTIONS #########################################################

x = []
y = []

def create_bokeh_figure(
    x: list,
    y: list
):
    bokeh_figure = figure(
        x_range=(0,len(x)),
        height=300,
        title="Example",
        toolbar_location=None,
        tools=""
    )
    bokeh_figure.vbar(x=x, top=y, width=0.9)
    bokeh_figure.xgrid.grid_line_color = None
    bokeh_figure.y_range.start = 0
    
    return bokeh_figure


# INTERACTIVE ELEMENTS #######################################################

def update_interactive_elements_lca(event):
    selected_activity = select_database_activity(search_string=widget_autocomplete_input_activity.value)
    widget_static_text.value = selected_activity['name']
    widget_tabulator.loading = True
    lca_score, df_activities = perform_lca_and_path_analysis(selected_activity=selected_activity)
    widget_tabulator.value = df_activities
    widget_tabulator.loading = False

def update_interactive_elements_temporalization(event):
    pane_bokeh.loading = True
    bokeh_figure = create_bokeh_figure(y=df_widget.value['float'])
    pane_bokeh.object = bokeh_figure
    pane_bokeh.loading = False

# https://panel.holoviz.org/reference/widgets/Button.html#buttonhttps://panel.holoviz.org/reference/widgets/Button.html#button
widget_button_activity.on_click(update_interactive_elements_lca)

# https://panel.holoviz.org/reference/widgets/Button.html#buttonhttps://panel.holoviz.org/reference/widgets/Button.html#button
widget_button_tabulator.on_click(update_interactive_elements_lca)

# https://panel.holoviz.org/reference/layouts/Column.html
pn.Column(
    widget_autocomplete_input_activity,
    widget_button_activity,
    widget_static_text,
    widget_tabulator,
).servable()
