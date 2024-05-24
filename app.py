# %%
import bw2io as bi
import bw2data as bd
import bw2calc as bc
from bw_graph_tools import NewNodeEachVisitGraphTraversal
import pandas as pd
import panel as pn
import numpy as np
from math import pi

from bokeh.palettes import Category20c, Category20
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.models import Div
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput

#https://panel.holoviz.org/developer_guide/extensions.html#extension-plugins
pn.extension()

# https://panel.holoviz.org/reference/widgets/Tabulator.html
pn.extension('tabulator')

# BRIGHTAY SETUP ################################################################
bi.bw2setup()

#list_of_useeio_method0_names1=([list(bd.methods)[0:19][i] for i in range (19)], ([str(list(bd.methods)[0:19][i]) for i in range (19)])) 


list_of_method0_names1=([list(bd.methods)[i] for i in range (len(list(bd.methods)))], ([str(list(bd.methods)[i]) for i in range (len(list(bd.methods)))])) 

list_of_database=['useeio_database','ecoinvent_database']

# PANEL SETUP ###################################################################

search_string =''
lca_score = 0
df_activities = pd.DataFrame()

# https://panel.holoviz.org/reference/widgets/AutocompleteInput.html
widget_autocomplete_input_database = pn.widgets.AutocompleteInput(
    name='Autocomplete Method Selection',
    options=list_of_database,
    case_sensitive=False,
    search_strategy='includes',
    placeholder='Write something her...',
    min_characters = 0
)
pn.Column(widget_autocomplete_input_database).servable()
#While waiting
widget_autocomplete_input_activity = pn.widgets.AutocompleteInput(
        name='Autocomplete Bug Selection',
        options=['Bug','Bug'],
        case_sensitive=False,
        search_strategy='includes',
        placeholder='Write something her...'
    )
if widget_autocomplete_input_database.value=='useeio_database' :
    # USEEIO
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

    # https://panel.holoviz.org/reference/widgets/AutocompleteInput.html
    widget_autocomplete_input_activity = pn.widgets.AutocompleteInput(
        name='Autocomplete Product Selection',
        options=list_of_useeio_products,
        case_sensitive=False,
        search_strategy='includes',
        placeholder='Write something her...'
    )
if widget_autocomplete_input_database.value=='ecoinvent_database' :
    # Ecoinvent : 
    # file path to the place with the ecoinvent spold files (datasets directory)
    def check_for_ecoinvent_brightway_project():
        fpei39 = "C://Users//Louis//Spring-School-Group-2//ecoinvent 3.9.1_cutoff_ecoSpold02//datasets"
        if 'ecoinvent 3.9.1 cutoff' in bd.databases:
            print("Database has already been imported")
        #del bw2data.databases["ecoinvent 3.9.1 cutoff"]
        else:
            ei39 = bi.SingleOutputEcospold2Importer(fpei39, 'ecoinvent 3.9.1 cutoff')
            ei39.apply_strategies()
            ei39.statistics()

        if len(list(ei39.unlinked)) == 0:
            ei39.write_database()
    ei=check_for_ecoinvent_brightway_project()

    list_of_ecoinvent_products=[
        node['name'] for node in ei
        if 'product' in node['type']
    ]
        # https://panel.holoviz.org/reference/widgets/AutocompleteInput.html
    widget_autocomplete_input_activity = pn.widgets.AutocompleteInput(
        name='Autocomplete Product Selection',
        options=list_of_ecoinvent_products,
        case_sensitive=False,
        search_strategy='includes',
        placeholder='Write something her...'
    )
list_of_method0_names1=([list(bd.methods)[i] for i in range (len(list(bd.methods)))], ([str(list(bd.methods)[i]) for i in range (len(list(bd.methods)))])) 
# https://panel.holoviz.org/reference/widgets/AutocompleteInput.html
widget_autocomplete_input_method = pn.widgets.AutocompleteInput(
    name='Autocomplete Method Selection',
    options=list_of_method0_names1[1],
    case_sensitive=False,
    search_strategy='includes',
    placeholder='Write something her...',
    min_characters = 0
)


#https://panel.holoviz.org/reference/widgets/Checkbox.html
widget_checkbox_market = pn.widgets.Checkbox(name='Market : automatic')

#https://panel.holoviz.org/reference/widgets/Checkbox.html
widget_checkbox_transport = pn.widgets.Checkbox(name='Transport : automatic')

#https://panel.holoviz.org/reference/widgets/ArrayInput.html
widget_amount_activity = pn.widgets.ArrayInput(name='Amount of Process', value=None)

#https://panel.holoviz.org/reference/widgets/ArrayInput.html
widget_amount_cut_off = pn.widgets.ArrayInput(name='Cut-off', value=None)

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
    selected_activity, name_method_chosen, list_of_method0_names1
) -> pd.DataFrame:
    # https://docs.brightway.dev/en/latest/content/gettingstarted/lca.html#calculate-one-lcia-result
    index = list_of_method0_names1[1].index(name_method_chosen)
    lca = bc.LCA(
        demand={selected_activity: 1},
        method=list_of_useeio_method0_names1[0][index] # globaJl climate change
    )
    lca.lci()
    lca.lcia()
    lca_score = round(lca.score,2)

    # https://docs.brightway.dev/projects/graphtools/en/latest/content/api/bw_graph_tools/graph_traversal/index.html#bw_graph_tools.graph_traversal.NewNodeEachVisitGraphTraversal
    graph_traversal_result = NewNodeEachVisitGraphTraversal.calculate(lca, cutoff=0.01)

    return lca_score, pd.DataFrame.from_dict(graph_traversal_result['nodes'], orient='index')

def updating_col_data_frame(
        df,
):
    df['Starting time of the process'] =[None]*df.shape[0]
    df['Ending time of the process'] = [None]*df.shape[0]
    df['Temporalization distribution'] = [None]*df.shape[0]
    return df

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


pane_bokeh = pn.pane.Bokeh(
    create_bokeh_figure(x,y),
    theme="dark_minimal"
)

# INTERACTIVE ELEMENTS #######################################################
#Test dataframe : 
'''
dic={'activity_name': {0: 'diesel, import from RoW',
  1: 'diesel production, petroleum refinery operation',
  2: 'market for petroleum',
  3: 'market for petroleum'},
 'consumer_name': {0: nan,
  1: 'diesel, import from RoW',
  2: 'diesel production, petroleum refinery operation',
  3: 'diesel production, petroleum refinery operation'},
 'direct_emissions_score': {0: 0.0,
  1: 0.19587872833787667,
  2: 1.6178466321291924e-05,
  3: 3.503027587087129e-05},
 'cumulative_score': {0: 0.8485333001862312,
  1: 0.7825854384256328,
  2: 0.1764999453369338,
  3: 0.40400083943338183},
 'cumulative_contribution': {0: 1.000000000000001,
  1: 0.9222801724503639,
  2: 0.20800591479226194,
  3: 0.4761166584089446}}
mon_df = pd.DataFrame.from_dict(dic)
'''
###
def update_interactive_elements_lca(event):
    selected_activity = select_database_activity(search_string=widget_autocomplete_input_activity.value)
    widget_static_text.value = selected_activity['name']
    widget_tabulator.loading = True
    lca_score, df_activities = perform_lca_and_path_analysis(selected_activity=selected_activity, name_method_chosen=widget_autocomplete_input_method.value, list_of_method0_names1=list_of_method0_names1)
    df_activities=updating_col_data_frame(df_activities)
    widget_tabulator.value = df_activities
    widget_tabulator.loading = False

def update_interactive_elements_temporalization(event):
    df_activities=widget_tabulator.value
    pane_bokeh.loading = True
    bokeh_figure = create_bokeh_figure(y=widget_tabulator.value['float'])
    pane_bokeh.object = bokeh_figure
    pane_bokeh.loading = False

# https://panel.holoviz.org/reference/widgets/Button.html#buttonhttps://panel.holoviz.org/reference/widgets/Button.html#button
widget_button_activity.on_click(update_interactive_elements_lca)

# https://panel.holoviz.org/reference/widgets/Button.html#buttonhttps://panel.holoviz.org/reference/widgets/Button.html#button
widget_button_tabulator.on_click(update_interactive_elements_temporalization)

# https://panel.holoviz.org/reference/layouts/Column.html
pn.Column(
    widget_autocomplete_input_activity,
    widget_autocomplete_input_method,
    widget_amount_activity,
    widget_amount_cut_off,
    widget_checkbox_market,
    widget_checkbox_transport,
    widget_button_activity,
    widget_static_text,
    widget_tabulator,
    widget_button_tabulator
).servable()
#%%
1