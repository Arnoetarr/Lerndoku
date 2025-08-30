from datetime import datetime, time

def berechne_arbeitsphase(jetzt=None):
    if jetzt is None:
        jetzt = datetime.now().time()

    phasen_start = [
        time(7, 30),  # 0. AP
        time(9, 0),   # 1. AP
        time(10, 30), # 2. AP
        time(12, 0),  # 3. AP
        time(13, 30), # 4. AP
        time(15, 0),  # 5. AP
        time(16, 30), # 6. AP
    ]

    for i, start in enumerate(reversed(phasen_start)):
        if jetzt >= start:
            return f"{len(phasen_start) - 1 - i}.AP"
    return "0.AP"
