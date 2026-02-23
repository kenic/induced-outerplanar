import pandas as pd
import matplotlib.pyplot as plt

# 入力CSV
path = "evolve_n200_greedyavg_summary.csv"  # パスは適宜変更

# 出力ファイル
out_png = "fig1_greedy_fitness_evolution.png"
out_pdf = "fig1_greedy_fitness_evolution.pdf"

df = pd.read_csv(path)

# 必要列チェック
needed = ["gen", "fit_mean", "fit_min", "survivor_fit_mean"]
missing = [c for c in needed if c not in df.columns]
if missing:
    raise ValueError(f"missing columns: {missing}")

x = df["gen"]

plt.figure()
plt.plot(x, df["fit_mean"], label="population mean (avg greedy)")
plt.plot(x, df["fit_min"], label="population min (avg greedy)")
plt.plot(x, df["survivor_fit_mean"], label="survivor mean (bottom_k)")
plt.xlabel("generation")
plt.ylabel("greedy ratio (average over runs)")
plt.legend()
plt.tight_layout()
plt.savefig(out_png, dpi=200)
plt.savefig(out_pdf)
plt.close()

print("wrote:", out_png)
print("wrote:", out_pdf)
