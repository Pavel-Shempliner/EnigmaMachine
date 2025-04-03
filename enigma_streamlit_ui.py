import streamlit as st
from enigma_machine_sim import (
    EnigmaMachine,
    Rotor,
    Reflector,
    Plugboard,
    ROTOR_WIRINGS,
    REFLECTOR_B,
)

st.set_page_config(page_title="Enigma Machine Simulator", layout="wide")
st.title("🔐 Enigma Machine Simulator")

# Initialize session state for persistent values
if "message_key" not in st.session_state:
    st.session_state.message_key = ""
if "encoded_key_twice" not in st.session_state:
    st.session_state.encoded_key_twice = ""
if "generate_new_key" not in st.session_state:
    st.session_state.generate_new_key = True
if "plaintext" not in st.session_state:
    st.session_state.plaintext = "HELLO WORLD"


def init_session_keys():
    if "pos1" not in st.session_state:
        st.session_state.pos1 = "A"
    if "pos2" not in st.session_state:
        st.session_state.pos2 = "A"
    if "pos3" not in st.session_state:
        st.session_state.pos3 = "A"


init_session_keys()

main_col1, main_col2 = st.columns([2, 1], gap="large")

with main_col1:

    def on_text_change():
        st.session_state.plaintext = st.session_state.input_text

    plaintext = st.text_input(
        "Enter your message:",
        value=st.session_state.plaintext,
        key="input_text",
        on_change=on_text_change,
    )

    rotor_choices = list(ROTOR_WIRINGS.keys())
    col1, col2, col3 = st.columns(3)
    with col1:
        rotor1 = st.selectbox("Rotor 1", rotor_choices, index=0, key="rotor1")
    with col2:
        rotor2 = st.selectbox("Rotor 2", rotor_choices, index=1, key="rotor2")
    with col3:
        rotor3 = st.selectbox("Rotor 3", rotor_choices, index=2, key="rotor3")

    col4, col5, col6 = st.columns(3)
    with col4:
        pos1 = st.selectbox(
            "Rotor 1 Position", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), index=0, key="pos1"
        )
    with col5:
        pos2 = st.selectbox(
            "Rotor 2 Position", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), index=0, key="pos2"
        )
    with col6:
        pos3 = st.selectbox(
            "Rotor 3 Position", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), index=0, key="pos3"
        )

    plugboard_input = st.text_input(
        "Plugboard Pairs (e.g., A:B,C:D):", "A:B,C:D", key="plugboard"
    )

    plugboard_pairs = {}
    try:
        if plugboard_input:
            for pair in plugboard_input.split(","):
                a, b = pair.strip().upper().split(":")
                plugboard_pairs[a] = b
                plugboard_pairs[b] = a
    except ValueError:
        st.warning("Invalid plugboard format. Use format like A:B,C:D")

    rotors = [
        Rotor(*ROTOR_WIRINGS[rotor1], position=pos1),
        Rotor(*ROTOR_WIRINGS[rotor2], position=pos2),
        Rotor(*ROTOR_WIRINGS[rotor3], position=pos3),
    ]
    reflector = Reflector(REFLECTOR_B)
    plugboard = Plugboard(plugboard_pairs)
    machine = EnigmaMachine(rotors, reflector, plugboard)

    if st.button("Encode / Decode"):
        output = machine.encode_message(plaintext)
        st.success(f"Output Message: {output}")
        machine.reset_rotors()
        roundtrip = machine.encode_message(output)
        st.info(f"Decoded (Round-trip): {roundtrip}")

with main_col2:
    st.markdown("### 🧾 Enigma Protocol Simulation")

    st.markdown("**Instructions:**")
    st.markdown("""
    1. Select the rotors (I–V), their order, and their initial positions
    2. Set plugboard swaps if needed (e.g., A↔B, C↔D)
    3. Type your message and click 'Encode / Decode'
    4. Use the same settings on the recipient's side to decode the message
    """)

    if st.session_state.get("message_key", "") == "" and st.session_state.get(
        "update_rotors", False
    ):
        st.error("No valid message key available. Generate a new key first.")
        st.session_state.update_rotors = False
