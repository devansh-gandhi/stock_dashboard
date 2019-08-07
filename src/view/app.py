import dash

app = dash.Dash('Stock Dashboard')
app.title = 'Stock Dashboard'
server = app.server
app.config.suppress_callback_exceptions = True