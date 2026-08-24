with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
skip = False
for line in lines:
    if "# Sort strictly by combined edge, not raw odds" in line:
        out.append("""      # Bucket by date (this week vs future) and then sort by odds
      from datetime import datetime, timedelta
      now = datetime.utcnow()
      seven_days = now + timedelta(days=7)
      
      def get_max_date(acca):
          max_d = now
          for leg in acca["legs"]:
              try:
                  d = datetime.strptime(leg["date"], "%Y-%m-%dT%H:%M:%SZ")
                  if d > max_d: max_d = d
              except: pass
          return max_d

      def sort_and_bucket(accas):
          this_week = []
          future = []
          for a in accas:
              if get_max_date(a) <= seven_days:
                  this_week.append(a)
              else:
                  future.append(a)
          this_week.sort(key=lambda x: abs(x["odds"] - 2.0))
          future.sort(key=lambda x: abs(x["odds"] - 2.0))
          return this_week + future

      accas_soccer = sort_and_bucket(accas_soccer)
      accas_nba = sort_and_bucket(accas_nba)
""")
        skip = True
    elif skip and "accas_nba.sort" in line:
        skip = False
    elif skip and "accas_soccer.sort" in line:
        pass
    else:
        out.append(line)

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "w", encoding="utf-8") as f:
    f.writelines(out)
