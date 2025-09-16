import ast
import operator
import os
import sys
import subprocess
from typing import Any, List, Optional


ALLOWED_OPERATORS = {
	ast.Add: operator.add,
	ast.Sub: operator.sub,
	ast.Mult: operator.mul,
	ast.Div: operator.truediv,
	ast.FloorDiv: operator.floordiv,
	ast.Mod: operator.mod,
	ast.Pow: operator.pow,
}


def _eval_ast(node: ast.AST) -> Any:
	"""Avalia uma AST com operações matemáticas básicas de forma segura."""
	if isinstance(node, ast.Expression):
		return _eval_ast(node.body)

	# Números (int, float)
	if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
		return node.value

	# Números (compat para Python <3.8, caso necessário)
	if hasattr(ast, "Num") and isinstance(node, getattr(ast, "Num")):
		return node.n  # type: ignore[attr-defined]

	# Operações binárias: a <op> b
	if isinstance(node, ast.BinOp):
		left = _eval_ast(node.left)
		right = _eval_ast(node.right)
		op_type = type(node.op)
		if op_type in ALLOWED_OPERATORS:
			# Tratamento de divisão por zero
			if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
				raise ZeroDivisionError("Divisão por zero não é permitida")
			return ALLOWED_OPERATORS[op_type](left, right)
		raise ValueError("Operador não suportado")

	# Operações unárias: +a, -a
	if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
		operand = _eval_ast(node.operand)
		return +operand if isinstance(node.op, ast.UAdd) else -operand

	# Parênteses são tratados pela própria árvore (ast.Expr/ast.BinOp aninhados)

	raise ValueError("Expressão inválida ou não suportada")


def safe_eval_math(expr: str) -> float:
	"""Avalia de forma segura uma expressão matemática limitada.

	Suporta: +, -, *, /, //, %, **, parênteses, números inteiros e decimais.
	"""
	try:
		tree = ast.parse(expr, mode="eval")
		return _eval_ast(tree)
	except ZeroDivisionError:
		raise
	except Exception as exc:  # noqa: BLE001
		raise ValueError(f"Expressão inválida: {exc}") from exc


def imprimir_menu() -> None:
	print("Calculadora - selecione uma opção:")
	print("  1) Soma (+)")
	print("  2) Subtração (-)")
	print("  3) Multiplicação (*)")
	print("  4) Divisão (/)")
	print("  5) Divisão inteira (//)")
	print("  6) Módulo (%)")
	print("  7) Potência (**)")
	print("  8) Avaliar expressão livre")
	print("  0) Sair")
	print("(Dicas: 'm' menu, 'h' histórico, 'c' copiar último resultado)")


def ler_numero(prompt: str) -> float:
	while True:
		valor = input(prompt).strip().replace(",", ".")
		try:
			return float(valor)
		except ValueError:
			print("Entrada inválida. Digite um número válido (use . ou , para decimais).")


def loop_interativo() -> None:
	imprimir_menu()
	op_map = {
		"1": (operator.add, "+"),
		"2": (operator.sub, "-"),
		"3": (operator.mul, "*"),
		"4": (operator.truediv, "/"),
		"5": (operator.floordiv, "//"),
		"6": (operator.mod, "%"),
		"7": (operator.pow, "**"),
	}
	# Histórico e último resultado
	historico: List[str] = []
	ultimo_resultado: Optional[float] = None

	while True:
		entrada = input("Seleção (0-8, 'm', 'h', 'c'): ").strip().lower()
		if entrada in {"0", "sair", "exit", "quit"}:
			print("Até mais!")
			break
		if entrada == "m":
			imprimir_menu()
			continue
		if entrada == "h":
			if not historico:
				print("Histórico vazio.")
				continue
			print("Histórico (mais recentes no fim):")
			for item in historico[-20:]:
				print("  ", item)
			continue
		if entrada == "c":
			if ultimo_resultado is None:
				print("Nenhum resultado para copiar.")
				continue
			# Copiar para clipboard
			try:
				if os.name == "nt":
					proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, close_fds=True)
					assert proc.stdin is not None
					proc.stdin.write(str(ultimo_resultado).encode("utf-16le"))
					proc.stdin.close()
					ok = proc.wait() == 0
				elif sys.platform == "darwin":
					ok = subprocess.run(["pbcopy"], input=str(ultimo_resultado).encode(), check=False).returncode == 0
				else:
					# Linux
					if subprocess.call(["which", "xclip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
						ok = subprocess.run(["xclip", "-selection", "clipboard"], input=str(ultimo_resultado).encode(), check=False).returncode == 0
					elif subprocess.call(["which", "xsel"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
						ok = subprocess.run(["xsel", "--clipboard", "--input"], input=str(ultimo_resultado).encode(), check=False).returncode == 0
					else:
						ok = False
			except Exception:
				ok = False
			print("Copiado para a área de transferência." if ok else "Não foi possível copiar automaticamente neste sistema.")
			continue

		# Opções 1-7: binárias
		if entrada in op_map:
			nome_op = op_map[entrada][1]
			try:
				a = ler_numero("A: ")
				b = ler_numero("B: ")
				if nome_op in {"/", "//", "%"} and b == 0:
					raise ZeroDivisionError("Divisão por zero não é permitida")
				resultado = op_map[entrada][0](a, b)
				print(f"Resultado: {resultado}")
				ultimo_resultado = float(resultado)
				historico.append(f"{a} {nome_op} {b} = {resultado}")
			except ZeroDivisionError as zde:
				print(f"Erro: {zde}")
			except Exception:
				print("Erro: entrada inválida.")
			continue

		# Opção 8: expressão livre
		if entrada == "8":
			expr = input("Expressão: ").strip()
			if not expr:
				continue
			try:
				resultado = safe_eval_math(expr)
				print(f"Resultado: {resultado}")
				ultimo_resultado = float(resultado)
				historico.append(f"{expr} = {resultado}")
			except ZeroDivisionError as zde:
				print(f"Erro: {zde}")
			except ValueError as ve:
				print(f"Erro: {ve}")
			continue

		print("Opção inválida. Digite 0-8 ou 'm'.")


if __name__ == "__main__":
	loop_interativo()


