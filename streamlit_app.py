import streamlit as st


def initialize_state() -> None:
    if "display" not in st.session_state:
        st.session_state.display = "0"
    if "previous_value" not in st.session_state:
        st.session_state.previous_value = None
    if "operation" not in st.session_state:
        st.session_state.operation = None
    if "waiting_for_operand" not in st.session_state:
        st.session_state.waiting_for_operand = False


MAX_DISPLAY_LENGTH = 12


def format_for_display(value: float) -> str:
    if value == float("inf"):
        return "Infinity"
    if value == float("-inf"):
        return "-Infinity"
    if value != value:  # NaN
        return "Error"
    s = str(value)
    if len(s) <= MAX_DISPLAY_LENGTH:
        return s
    if "." in s:
        integer_part, decimal_part = s.split(".", 1)
        available_decimals = MAX_DISPLAY_LENGTH - len(integer_part) - 1
        if available_decimals > 0:
            return f"{value:.{min(available_decimals, len(decimal_part))}f}"
    return f"{value:.6e}"


def input_number(num: str) -> None:
    if st.session_state.waiting_for_operand:
        st.session_state.display = num
        st.session_state.waiting_for_operand = False
        return
    new_display = num if st.session_state.display == "0" else st.session_state.display + num
    effective_length = new_display.replace(".", "").replace("-", "")
    if len(effective_length) <= MAX_DISPLAY_LENGTH:
        st.session_state.display = new_display


def calculate(first_value: float, second_value: float, operation: str) -> float:
    if operation == "+":
        return first_value + second_value
    if operation == "-":
        return first_value - second_value
    if operation == "*":
        return first_value * second_value
    if operation == "/":
        return first_value / second_value
    if operation == "=":
        return second_value
    return second_value


def input_operation(next_operation: str) -> None:
    try:
        input_value = float(st.session_state.display)
    except ValueError:
        input_value = 0.0
    if st.session_state.previous_value is None:
        st.session_state.previous_value = input_value
    elif st.session_state.operation:
        current_value = st.session_state.previous_value or 0.0
        new_value = calculate(current_value, input_value, st.session_state.operation)
        st.session_state.display = format_for_display(new_value)
        st.session_state.previous_value = new_value
    st.session_state.waiting_for_operand = True
    st.session_state.operation = next_operation


def perform_calculation() -> None:
    try:
        input_value = float(st.session_state.display)
    except ValueError:
        input_value = 0.0
    if st.session_state.previous_value is not None and st.session_state.operation:
        new_value = calculate(st.session_state.previous_value, input_value, st.session_state.operation)
        st.session_state.display = format_for_display(new_value)
        st.session_state.previous_value = None
        st.session_state.operation = None
        st.session_state.waiting_for_operand = True


def clear() -> None:
    st.session_state.display = "0"
    st.session_state.previous_value = None
    st.session_state.operation = None
    st.session_state.waiting_for_operand = False


def backspace() -> None:
    d = str(st.session_state.display)
    st.session_state.display = d[:-1] if len(d) > 1 else "0"


def render_button(label: str, on_click=None, args=None, key: str | None = None, type_: str = "default") -> None:
    style_map = {
        "op": "background-color:#ea580c;color:#fff;font-weight:600;border-radius:10px;height:48px;width:100%;",
        "danger": "background-color:#ef4444;color:#fff;font-weight:600;border-radius:10px;height:48px;width:100%;",
        "gray": "background-color:#6b7280;color:#fff;font-weight:600;border-radius:10px;height:48px;width:100%;",
        "default": "background-color:#374151;color:#fff;font-weight:600;border-radius:10px;height:48px;width:100%;",
    }
    st.markdown(
        f"<div style='display:flex'><button style='{style_map.get(type_, style_map["default"]) }' onclick=''></button></div>",
        unsafe_allow_html=True,
    )
    st.button(label, key=key, on_click=on_click, args=args or [])


def main() -> None:
    st.set_page_config(page_title="Calculadora", page_icon="🧮", layout="centered")
    initialize_state()

    st.markdown(
        """
        <style>
        .calculator-card {max-width: 420px; margin: 24px auto; background:#111827; border:1px solid #334155; border-radius:12px; padding:16px; box-shadow:0 10px 30px rgba(0,0,0,.35)}
        .calc-title { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; color:#e5e7eb; font-weight:600 }
        .display { background:#1f2937; border:1px solid #334155; border-radius:10px; padding:14px 12px; margin:10px 0 14px; text-align:right }
        .display-main { font-family: ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace; font-size:28px; color:#e5e7eb; word-break:break-all }
        .display-sub { color:#f59e0b; font-size:12px; margin-top:4px }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='calculator-card'>", unsafe_allow_html=True)
    st.markdown("<div class='calc-title'>Calculadora <span></span></div>", unsafe_allow_html=True)
    st.markdown("<div class='display'>", unsafe_allow_html=True)
    st.markdown(f"<div class='display-main'>{st.session_state.display}</div>", unsafe_allow_html=True)
    if st.session_state.operation and st.session_state.previous_value is not None:
        st.markdown(
            f"<div class='display-sub'>{st.session_state.previous_value} {st.session_state.operation}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Grid de botões 4xN
    # Linha 1: C, ←, ÷ (largura dupla)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button("C", use_container_width=True, on_click=clear)
    with c2:
        st.button("←", use_container_width=True, on_click=backspace)
    with c3:
        st.button("÷", use_container_width=True, on_click=input_operation, args=("/",))
    with c4:
        st.write("")

    # 7 8 9 *
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button("7", use_container_width=True, on_click=input_number, args=("7",))
    with c2:
        st.button("8", use_container_width=True, on_click=input_number, args=("8",))
    with c3:
        st.button("9", use_container_width=True, on_click=input_number, args=("9",))
    with c4:
        st.button("×", use_container_width=True, on_click=input_operation, args=("*",))

    # 4 5 6 -
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button("4", use_container_width=True, on_click=input_number, args=("4",))
    with c2:
        st.button("5", use_container_width=True, on_click=input_number, args=("5",))
    with c3:
        st.button("6", use_container_width=True, on_click=input_number, args=("6",))
    with c4:
        st.button("-", use_container_width=True, on_click=input_operation, args=("-",))

    # 1 2 3 +
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button("1", use_container_width=True, on_click=input_number, args=("1",))
    with c2:
        st.button("2", use_container_width=True, on_click=input_number, args=("2",))
    with c3:
        st.button("3", use_container_width=True, on_click=input_number, args=("3",))
    with c4:
        st.button("+", use_container_width=True, on_click=input_operation, args=("+",))

    # 0 (duplo), ., =
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button("0", use_container_width=True, on_click=input_number, args=("0",))
    with c2:
        st.button("0", use_container_width=True, on_click=input_number, args=("0",))
    with c3:
        if "." not in str(st.session_state.display):
            st.button(",", use_container_width=True, on_click=input_number, args=(".",))
        else:
            st.write("")
    with c4:
        st.button("=", use_container_width=True, on_click=perform_calculation)

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()


