import random
import re

EMAIL = re.compile(r"\b[\w.+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b")

FIRST = ["maya", "owen", "lena", "hugo", "nora", "felix", "ines", "theo", "zara", "caleb", "chidi",  
         "ngozi", "tunde", "amaka", "emeka", "funmi", "bola", "ife", "sade", "kelechi"]

LAST = ["brandt", "okafor", "lindqvist", "ferreira", "tanaka", "novak", "haddad", "mercer",
        "adeyemi", "okonkwo", "balogun", "eze", "abubakar", "ogunleye", "nwosu", "bello"]
PROVIDERS = ["quickmail", "numbus", "postbox", "mailhub", "inboxly", "zephyr", "lumen", "parcel"]
TLDS = ["test", "example", "invalid"]

def fake_email(rng):
    first, last = rng.choice(FIRST), rng.choice(LAST)
    local = rng.choice([f"{first}.{last}", f"{first[0]}{last}", f"{first}_{last}{rng.randint(1,99)}"])
    return f"{local}@{rng.choice(PROVIDERS)}.{rng.choice(TLDS)}"

def sanitize(text, rng):
    seen = {}

    def swap(match):
        key = match.group(0).lower()
        if key not in seen:
            seen[key] = fake_email(rng)
        return seen[key]

    return EMAIL.sub(swap,text)

if __name__ == "__main__":
    text = "Mail kpk22128@gmail.com or KPK22128@gmail.com, cc a.b@corp.io. Build opsgenie@1.3.13 ok."
    out = sanitize(text, random.Random(0))
    print(out)
    assert "gmail.com" not in out and "corp.io" not in out
    assert "opsgenie@1.3.13" in out
    assert out.split()[1] == out.split()[3].rstrip(",")
    assert sanitize (text, random.Random(0)) == out
    assert sanitize (text, random.Random(1)) != out
    print("ok")