import streamlit as st
from enigma_machine_sim import EnigmaMachine, Rotor, Reflector, Plugboard, ROTOR_WIRINGS, REFLECTOR_B

st.set_page_config(page_title="Enigma Machine Simulator")
st.title("🔐 Enigma Machine Simulator")

# Input fields
plaintext = st.text_input("Enter your message:", "HELLO WORLD")
rotor_choices = list(ROTOR_WIRINGS.keys())

col1, col2, col3 = st.columns(3)
with col1:
    rotor1 = st.selectbox("Rotor 1", rotor_choices, index=0)
with col2:
    rotor2 = st.selectbox("Rotor 2", rotor_choices, index=1)
with col3:
    rotor3 = st.selectbox("Rotor 3", rotor_choices, index=2)

col4, col5, col6 = st.columns(3)
with col4:
    pos1 = st.selectbox("Rotor 1 Position", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), index=0)
with col5:
    pos2 = st.selectbox("Rotor 2 Position", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), index=0)
with col6:
    pos3 = st.selectbox("Rotor 3 Position", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), index=0)

plugboard_input = st.text_input("Plugboard Pairs (e.g., A:B,C:D):", "A:B,C:D")

# Parse plugboard
plugboard_pairs = {}
try:
    if plugboard_input:
        for pair in plugboard_input.split(','):
            a, b = pair.strip().upper().split(':')
            plugboard_pairs[a] = b
            plugboard_pairs[b] = a
except ValueError:
    st.warning("Invalid plugboard format. Use format like A:B,C:D")

# Setup machine
rotors = [
    Rotor(*ROTOR_WIRINGS[rotor1], position=pos1),
    Rotor(*ROTOR_WIRINGS[rotor2], position=pos2),
    Rotor(*ROTOR_WIRINGS[rotor3], position=pos3)
]

reflector = Reflector(REFLECTOR_B)
plugboard = Plugboard(plugboard_pairs)
machine = EnigmaMachine(rotors, reflector, plugboard)

# Encode
if st.button("Encode"):
    encoded = machine.encode_message(plaintext)
    st.success(f"Encoded Message: {encoded}")

    machine.reset_rotors()
    decoded = machine.encode_message(encoded)
    st.info(f"Decoded (Round-trip): {decoded}")
