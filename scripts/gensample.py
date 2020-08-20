from random import choice
with open(f"sample.txt", "w") as out:
    for i in range(11):
        with open(f"data{i+1}.txt", "r") as file:
            lines = file.readlines()
            for l in range(2000):
                sel = choice(lines)
                out.write(sel)
