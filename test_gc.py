import language_tool_python as lt
tool = lt.LanguageTool('it', remote_server='http://localhost:8082')
print([m.ruleId for m in tool.check("quando gli e l'hanno diagnostico")])
tool.close()