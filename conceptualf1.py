import matplotlib.pyplot as plt
import numpy as np

# Conceptual data for F1 Scores by Disaster Type
disaster_types = ['Flood', 'Fire', 'Traffic', 'Earthquake']
f1_scores = [0.92, 0.88, 0.85, 0.80]
colors = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd']

# Create the figure
plt.figure(figsize=(9, 6))
bars = plt.bar(disaster_types, f1_scores, color=colors)

# Add titles and labels
plt.title("Figure 4: Classification Performance: F1 Score per Disaster Type", fontsize=14)
plt.ylabel("F1 Score", fontsize=12)
plt.xlabel("Disaster Type", fontsize=12)
plt.ylim(0, 1.0) 

# Add data labels on top of the bars
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.01, round(yval, 2), ha='center', va='bottom', fontsize=11)

plt.tight_layout()

# Save the figure
plt.savefig("F1_Score_Performance.png")
print("F1_Score_Performance.png generated successfully.")