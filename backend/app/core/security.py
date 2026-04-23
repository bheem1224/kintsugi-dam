import ast


class SecurityViolationError(Exception):
    """Raised when an AST check detects potentially dangerous operations."""

    pass


class SecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.dangerous_functions = {
            "os": {"remove", "unlink"},
            "shutil": {"move", "rmtree", "copy"},
        }
        self.safe_modes = {"r", "rb", "rt"}
        self.blocked_builtins = {"eval", "exec", "getattr", "setattr", "__import__"}
        self.blocked_modules = {"os", "sys", "subprocess", "shutil"}

    def visit_Import(self, node):
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module in self.blocked_modules:
                raise SecurityViolationError(
                    f"Importing blocked module '{alias.name}' detected at line {node.lineno}."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module in self.blocked_modules:
                raise SecurityViolationError(
                    f"Importing from blocked module '{node.module}' detected at line {node.lineno}."
                )
        self.generic_visit(node)

    def visit_Call(self, node):
        func = node.func

        # Block specific built-in function calls
        if isinstance(func, ast.Name):
            if func.id in self.blocked_builtins:
                raise SecurityViolationError(
                    f"Use of blocked built-in '{func.id}' detected at line {node.lineno}."
                )

            # Check for standard open() call
            if func.id == "open":
                mode_val = "r"

                # Check positional args
                if len(node.args) >= 2:
                    mode_arg = node.args[1]
                    if isinstance(mode_arg, ast.Constant):
                        mode_val = mode_arg.value

                # Check keyword args
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode_val = kw.value

                if mode_val not in self.safe_modes:
                    raise SecurityViolationError(
                        f"Potentially dangerous 'open' mode '{mode_val}' detected at line {node.lineno}."
                    )

        # Check for os or shutil module calls (fallback for unaliased cases)
        elif isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name):
                module_name = func.value.id
                func_name = func.attr

                if (
                    module_name in self.dangerous_functions
                    and func_name in self.dangerous_functions[module_name]
                ):
                    raise SecurityViolationError(
                        f"Potentially dangerous function call '{module_name}.{func_name}' detected at line {node.lineno}."
                    )

        self.generic_visit(node)


def validate_plugin_ast(file_path: str) -> None:
    """
    Parses a Python file into an AST and checks for dangerous file operations.
    Raises SecurityViolationError if modifications are detected.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=file_path)
    visitor = SecurityVisitor()
    visitor.visit(tree)
