import ast
import operator
import os
import sys
import subprocess
import tkinter as tk
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


class CalculatorGUI:
	"""Interface gráfica com botões redondos e estilos customizados."""

	COLOR_YELLOW = "#FFD700"
	COLOR_BLACK = "#000000"
	COLOR_RED = "#FF0000"
	COLOR_DARK_BLUE = "#00008B"
	COLOR_LIGHT_BLUE = "#ADD8E6"

	def __init__(self) -> None:
		self.root = tk.Tk()
		self.root.title("Calculadora")
		self.expression: str = ""

		self.display = tk.Label(self.root, text="", anchor="e", font=("Segoe UI", 20), bg="white", fg="#333")
		self.display.pack(fill="x", padx=12, pady=(12, 8))

		self.canvas = tk.Canvas(self.root, width=340, height=420, bg="#f7f7f7", highlightthickness=0)
		self.canvas.pack(padx=12, pady=12)

		self._draw_buttons()
		self.canvas.bind("<Button-1>", self._on_click)

	def _set_text(self, text: str) -> None:
		self.display.config(text=text)

	def _append(self, token: str) -> None:
		self.expression += token
		self._set_text(self.expression)

	def _eval(self) -> None:
		if not self.expression:
			return
		try:
			resultado = safe_eval_math(self.expression)
			self.expression = str(resultado)
			self._set_text(self.expression)
		except ZeroDivisionError:
			self._set_text("Erro: div/zero")
			self.expression = ""
		except Exception:
			self._set_text("Expressão inválida")
			self.expression = ""

	def _draw_circle(self, cx: int, cy: int, r: int, fill: str, outline: str, text: str, text_color: str, tag: str) -> None:
		oval_id = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline=outline, width=3, tags=(tag, "hit"))
		self.canvas.create_text(cx, cy, text=text, fill=text_color, font=("Segoe UI", 16, "bold"), tags=(tag, "hit"))

	def _draw_buttons(self) -> None:
		# Números 1-9 em grade 3x3
		r = 38
		x0, y0 = 70, 110  # offsets
		dx, dy = 100, 90
		num = 1
		for row in range(3):
			for col in range(3):
				cx = x0 + col * dx
				cy = y0 + row * dy
				self._draw_circle(
					cx,
					cy,
					r,
					fill=self.COLOR_YELLOW,
					outline=self.COLOR_YELLOW,
					text=str(num),
					text_color=self.COLOR_BLACK,
					tag=f"num_{num}",
				)
				num += 1

		# Operações: +, -, *, /
		op_r = 34
		op_x = 270
		ops = [("+", 110), ("-", 200), ("*", 290), ("/", 380)]
		for symbol, cy in ops:
			self._draw_circle(
				op_x,
				cy,
				op_r,
				fill=self.COLOR_YELLOW,
				outline=self.COLOR_RED,
				text=symbol,
				text_color=self.COLOR_DARK_BLUE,
				tag=f"op_{symbol}",
			)

		# Botão igual
		self._draw_circle(
			170,
			380,
			40,
			fill=self.COLOR_LIGHT_BLUE,
			outline=self.COLOR_LIGHT_BLUE,
			text="=",
			text_color=self.COLOR_RED,
			tag="eq",
		)

	def _on_click(self, event: tk.Event) -> None:  # type: ignore[name-defined]
		items = self.canvas.find_withtag("current")
		if not items:
			return
		tags = self.canvas.gettags(items[0])
		# Número
		for t in tags:
			if t.startswith("num_"):
				self._append(t.split("_", 1)[1])
				return
			if t.startswith("op_"):
				op = t.split("_", 1)[1]
				self._append(op)
				return
			if t == "eq":
				self._eval()
				return

	def run(self) -> None:
		self.root.mainloop()


if __name__ == "__main__":
	# Inicia a interface gráfica
	CalculatorGUI().run()


