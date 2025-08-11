import compileall

assert compileall.compile_dir(".", force=True, quiet=1), "Syntax errors detected"
