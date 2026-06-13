import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Measured values from CubeIDE debugger (n=1000, STM32F407 @ 168 MHz)
mean_us = 787.05
min_us  = 787.05
max_us  = 787.07

fig, ax = plt.subplots(figsize=(8, 4))

# Shaded band showing the total observed range
ax.axvspan(min_us, max_us, color='steelblue', alpha=0.25, label='Observed range')

# Mean and WCET lines
ax.axvline(mean_us, color='orange', linestyle='--', linewidth=2,
           label=f'Mean  {mean_us:.2f} µs')
ax.axvline(max_us,  color='red',    linestyle='--', linewidth=2,
           label=f'WCET  {max_us:.2f} µs')

# Key result box
ax.text(0.02, 0.95,
        'All 1000 samples: 787.05 – 787.07 µs\n'
        'Range = 0.02 µs  (~3 cycles @ 168 MHz)\n'
        'σ ≈ 0  —  fully deterministic',
        transform=ax.transAxes,
        fontsize=9, color='dimgray',
        va='top', ha='left',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                  edgecolor='lightgray', alpha=0.9))

ax.set_xlim(786.5, 787.5)
ax.set_ylim(0, 1)
ax.set_xlabel('Inference latency (µs)')
ax.set_yticks([])                          # no y-axis — there are no counts to show
ax.set_title('HAR INT8 Inference — STM32F407 @ 168 MHz  (n=1000)')
ax.legend(loc='upper right')
ax.spines[['top', 'right', 'left']].set_visible(False)

plt.tight_layout()
plt.savefig('latency_histogram.png', dpi=150)
plt.show()