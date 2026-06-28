import matplotlib.pyplot as plt

# Measured values from CubeIDE debugger (n=1000, STM32F407 @ 168 MHz)
# Real UCI HAR test samples, 12 samples cycling through all 6 activity classes
mean_us  = 786.73
min_us   = 786.58
max_us   = 786.89
sigma_us = 2.24

fig, ax = plt.subplots(figsize=(8, 4))

# Shaded band showing the total observed range
ax.axvspan(min_us, max_us, color='steelblue', alpha=0.25, label='Observed range')

# Mean and WCET lines
ax.axvline(mean_us, color='orange', linestyle='--', linewidth=2,
           label=f'Mean {mean_us:.2f} µs')
ax.axvline(max_us, color='red', linestyle='--', linewidth=2,
           label=f'WCET {max_us:.2f} µs')

# Key result box
ax.text(0.02, 0.95,
        f'All 1000 samples: {min_us:.2f} – {max_us:.2f} µs\n'
        f'Range = {max_us - min_us:.2f} µs\n'
        f'σ = {sigma_us:.2f} µs — real UCI HAR input data\n'
        '12 samples × 6 activity classes',
        transform=ax.transAxes,
        fontsize=9, color='dimgray',
        va='top', ha='left',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                  edgecolor='lightgray', alpha=0.9))

ax.set_xlim(785.5, 788.0)
ax.set_ylim(0, 1)
ax.set_xlabel('Inference latency (µs)')
ax.set_yticks([])
ax.set_title('HAR INT8 Inference — STM32F407 @ 168 MHz (n=1000)\nReal UCI HAR input data, all 6 activity classes')
ax.legend(loc='upper right')
ax.spines[['top', 'right', 'left']].set_visible(False)

plt.tight_layout()
plt.savefig('latency_histogram.png', dpi=150)
print("Saved latency_histogram.png")
plt.show()