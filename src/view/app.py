import dash

app = dash.Dash(__name__)
app.title = 'Stock Dashboard'
server = app.server
app.config.suppress_callback_exceptions = True