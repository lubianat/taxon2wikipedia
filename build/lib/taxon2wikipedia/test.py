import re

wikipage = "Planta epifítica 0.9–23 centímetros altura. "
wikipage = re.sub(r" ([0-9|\.]+)–([0-9|\.]+)", " de \\1 a \\2", wikipage)

print(wikipage)
