with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(len(lines)):
    if lines[i].startswith("      # Bucket by date"):
        # Fix indentation of the block (from 6 spaces to 4 spaces)
        start = i
        while i < len(lines) and lines[i].startswith("      "):
            lines[i] = lines[i][2:]
            i += 1
        break

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "w", encoding="utf-8") as f:
    f.writelines(lines)
