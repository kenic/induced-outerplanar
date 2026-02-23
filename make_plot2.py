import pandas as pd
import matplotlib.pyplot as plt

summary_path = "evolve_n200_greedyavg_summary.csv"  # 適宜パス調整
df = pd.read_csv(summary_path)

out_png = "fig2_ls_confirm_min_over_gens.png"
out_pdf = "fig2_ls_confirm_min_over_gens.pdf"

plt.figure()
plt.plot(df["gen"], df["ls_confirm_min_bottom20"], label="LS confirm min (bottom20)")
plt.axhline(0.75, linestyle="--", label="0.75")
plt.xlabel("generation")
plt.ylabel("LS-improved ratio")
plt.legend()
plt.tight_layout()
plt.savefig(out_png, dpi=200)
plt.savefig(out_pdf)
plt.close()

print("wrote:", out_png)
print("wrote:", out_pdf)
