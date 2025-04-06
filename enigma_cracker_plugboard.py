import itertools
import logging
import string
import random
import math

from enigma_machine_sim import (
    REFLECTOR_B,
    ROTOR_WIRINGS,
    EnigmaMachine,
    Plugboard,
    Reflector,
    Rotor,
)
from tqdm import tqdm

logger = logging.getLogger(__name__)


def decrypt_message(ciphertext, rotor_ids, rotor_position, plugboard_config):
    """
    Decrypt the ciphertext using the specified rotor setting, rotor positions,
    and plugboard configuration.
    """
    reflector = Reflector(REFLECTOR_B)
    rotors = [
        Rotor(*ROTOR_WIRINGS[rotor_ids[0]], position=rotor_position[0]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[1]], position=rotor_position[1]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[2]], position=rotor_position[2]),
    ]
    machine = EnigmaMachine(rotors, reflector, Plugboard(plugboard_config))
    return machine.encode_message(ciphertext)


def score_text(text, crib):
    """
    A very simple scoring function.

    It gives a large bonus if the crib appears in the text,
    and adds a basic measure based on vowel frequency.

    In a real application, you might use quadgram statistics or
    another language model to score the plaintext.
    """
    score = 0
    if crib in text:
        score += 1000  # Crib bonus
    # Add a crude English-likeness score: count vowels
    vowels = "AEIOU"
    score += sum(text.count(v) for v in vowels)
    return score


def generate_neighbor(plugboard):
    """
    Generate a neighboring plugboard configuration by swapping letters between two pairs.

    The plugboard is represented as a dictionary where each paired letter maps to its partner.
    For example, {'A': 'B', 'B': 'A', 'C': 'D', 'D': 'C'} represents two pairs.
    """
    # Extract pairs as a list of tuples (each pair appears once).
    pairs = []
    seen = set()
    for k, v in plugboard.items():
        if k not in seen:
            pairs.append((k, v))
            seen.add(k)
            seen.add(v)
    # If fewer than two pairs exist, we cannot swap so return the same configuration.
    if len(pairs) < 2:
        return plugboard

    # Randomly select two pairs.
    p1, p2 = random.sample(pairs, 2)
    # Randomly choose one of two swap methods.
    if random.random() < 0.5:
        new_pair1 = (p1[0], p2[0])
        new_pair2 = (p1[1], p2[1])
    else:
        new_pair1 = (p1[0], p2[1])
        new_pair2 = (p1[1], p2[0])
    # Prevent self-mapping (a letter mapping to itself).
    if new_pair1[0] == new_pair1[1] or new_pair2[0] == new_pair2[1]:
        return plugboard

    # Create a new plugboard configuration.
    new_plugboard = plugboard.copy()
    # Remove the old mappings.
    for a, b in [p1, p2]:
        new_plugboard.pop(a, None)
        new_plugboard.pop(b, None)
    # Add the new pairs (in both directions).
    new_plugboard[new_pair1[0]] = new_pair1[1]
    new_plugboard[new_pair1[1]] = new_pair1[0]
    new_plugboard[new_pair2[0]] = new_pair2[1]
    new_plugboard[new_pair2[1]] = new_pair2[0]
    return new_plugboard


def simulated_annealing_plugboard_search(
    ciphertext,
    crib,
    rotor_ids,
    rotor_position,
    initial_plugboard,
    num_iterations=10000,
    start_temp=10.0,
    cooling_rate=0.0001,
):
    """
    Given a ciphertext, crib, rotor configuration, and an initial plugboard guess,
    use simulated annealing to search for a plugboard configuration that yields a
    better (more English-like) decryption.

    Returns the best plugboard configuration found and its score.
    """
    current_plugboard = initial_plugboard
    current_decryption = decrypt_message(
        ciphertext, rotor_ids, rotor_position, current_plugboard
    )
    current_score = score_text(current_decryption, crib)
    best_plugboard = current_plugboard
    best_score = current_score
    temp = start_temp

    for iteration in range(num_iterations):
        neighbor = generate_neighbor(current_plugboard)
        neighbor_decryption = decrypt_message(
            ciphertext, rotor_ids, rotor_position, neighbor
        )
        neighbor_score = score_text(neighbor_decryption, crib)
        delta = neighbor_score - current_score

        # Accept the neighbor if it's better, or with a probability if worse.
        if delta > 0 or random.random() < math.exp(delta / temp):
            current_plugboard = neighbor
            current_score = neighbor_score

        if current_score > best_score:
            best_plugboard = current_plugboard
            best_score = current_score

        temp *= 1 - cooling_rate
        # Optionally, exit early if the crib is found.
        if crib in decrypt_message(
            ciphertext, rotor_ids, rotor_position, best_plugboard
        ):
            break

    return best_plugboard, best_score


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # For demonstration, assume we already have candidate rotor settings.
    # In a real attack these would be found in a preliminary stage.
    rotor_ids = ("I", "II", "III")
    rotor_position = "AAA"  # example initial rotor positions

    # Suppose the true plugboard used for encryption is as follows.
    true_plugboard = {"A": "B", "B": "A", "C": "D", "D": "C"}

    plaintext = "HELLOWORLD"

    # Encrypt the plaintext with the known settings.
    test_rotors = [
        Rotor(*ROTOR_WIRINGS[rotor_ids[0]], position=rotor_position[0]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[1]], position=rotor_position[1]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[2]], position=rotor_position[2]),
    ]
    test_reflector = Reflector(REFLECTOR_B)
    test_plugboard = Plugboard(true_plugboard)
    test_machine = EnigmaMachine(test_rotors, test_reflector, test_plugboard)
    ciphertext = test_machine.encode_message(plaintext)
    print("Generated Ciphertext:", ciphertext)

    # Assume the rotor settings/positions are known from a prior search.
    # Now we attack the plugboard. We start with an initial guess.
    # (For demonstration we begin with the same pairs as the true plugboard,
    #  but in practice this would be an informed or random guess.)
    initial_plugboard = {"A": "B", "B": "A", "C": "D", "D": "C"}

    crib = "HELLO"
    best_plugboard, best_score = simulated_annealing_plugboard_search(
        ciphertext, crib, rotor_ids, rotor_position, initial_plugboard
    )

    final_decryption = decrypt_message(
        ciphertext, rotor_ids, rotor_position, best_plugboard
    )
    print("Best Plugboard Configuration Found:", best_plugboard)
    print("Final Decryption:", final_decryption)
