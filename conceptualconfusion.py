import matplotlib.pyplot as plt
import numpy as np
import itertools

# Conceptual Confusion Matrix Data (Sum of all cells = 100 conceptual test reports)
# Rows: Actual Class; Columns: Predicted Class
# Classes: Flood (0), Fire (1), Traffic (2), None/Other (3)
cm = np.array([
    [28, 1, 0, 1],   # Actual Flood: 28 TP, 2 FNs
    [0, 20, 0, 0],   # Actual Fire: 20 TP, 0 FNs
    [2, 0, 23, 0],   # Actual Traffic: 23 TP, 2 FPs
    [1, 1, 1, 22]    # Actual None: 22 TNs
])

classes = ['Flood', 'Fire', 'Traffic', 'None/Other']

plt.figure(figsize=(8, 7))
plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
plt.title("Figure 5: Conceptual Confusion Matrix (N=100)", fontsize=14)
plt.colorbar()
tick_marks = np.arange(len(classes))
plt.xticks(tick_marks, classes, rotation=45)
plt.yticks(tick_marks, classes)

# Normalize the confusion matrix for better visualization (optional but standard)
cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

thresh = cm.max() / 2.
for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
    plt.text(j, i, format(cm[i, j], 'd'),
             horizontalalignment="center",
             color="white" if cm[i, j] > thresh else "black",
             fontsize=12)

plt.tight_layout()
plt.ylabel('True Class (Actual)', fontsize=12)
plt.xlabel('Predicted Class (Model Output)', fontsize=12)

# Save the figure
plt.savefig("Confusion_Matrix.png")
print("Confusion_Matrix.png generated successfully.")