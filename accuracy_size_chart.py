import matplotlib.pyplot as plt
import numpy as np

# --- Data ---
labels = ['FP32 Model', 'INT8 Model']
accuracy = [94.67, 94.67]
size_kb = [479.0, 42.5]

x = np.arange(len(labels))
width = 0.35

fig, ax1 = plt.subplots(figsize=(7, 5))
fig.patch.set_facecolor('white')

# --- Accuracy bars (left axis) ---
bars1 = ax1.bar(x - width/2, accuracy, width,
                label='Accuracy (%)',
                color=['#2196F3', '#4CAF50'],
                edgecolor='white', linewidth=0.8)

ax1.set_ylabel('Accuracy (%)', fontsize=12)
ax1.set_ylim(0, 105)
ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=12)
ax1.tick_params(axis='y', labelcolor='#333333')

# Accuracy value labels
for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{bar.get_height():.2f}%', ha='center', va='bottom',
             fontsize=10, fontweight='bold')

# --- Size bars (right axis) ---
ax2 = ax1.twinx()
bars2 = ax2.bar(x + width/2, size_kb, width,
                label='Model Size (KB)',
                color=['#FF9800', '#F44336'],
                edgecolor='white', linewidth=0.8, alpha=0.85)

ax2.set_ylabel('Model Size (KB)', fontsize=12)
ax2.set_ylim(0, 600)
ax2.tick_params(axis='y', labelcolor='#333333')

# Size value labels
for bar in bars2:
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
             f'{bar.get_height():.1f} KB', ha='center', va='bottom',
             fontsize=10, fontweight='bold')

# --- Size reduction annotation ---
ax2.annotate('', xy=(x[1] + width/2, size_kb[1] + 60),
             xytext=(x[0] + width/2, size_kb[0] - 60),
             arrowprops=dict(arrowstyle='<->', color='#333333', lw=1.5))
ax2.text(1.0, 260, '11.3× smaller\n0% accuracy loss',
         ha='center', fontsize=9, color='#333333',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#f5f5f5',
                   edgecolor='#cccccc'))

# --- Legend and title ---
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2,
           loc='upper center', fontsize=9, framealpha=0.9)

ax1.set_title('Quantization Impact: FP32 vs INT8\nSTM32F407 HAR Classifier',
              fontsize=13, fontweight='bold', pad=12)

ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax1.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('accuracy_size_chart.png', dpi=150, bbox_inches='tight')
print("Saved accuracy_size_chart.png")
plt.show()