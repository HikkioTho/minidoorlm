import csv
import matplotlib.pyplot as plt


steps = []
train_losses = []
val_losses = []

with open("training_log.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        steps.append(int(row["step"]))
        train_losses.append(float(row["train_loss"]))
        val_losses.append(float(row["val_loss"]))

plt.figure(figsize=(10, 6))

plt.plot(steps, train_losses, label="Training Loss")
plt.plot(steps, val_losses, label="Validation Loss")

plt.title("MiniDoorLM Training Loss")
plt.xlabel("Training Step")
plt.ylabel("Loss")
plt.legend()
plt.grid(True)

plt.savefig("training_loss.png")
plt.show()

print("Saved graph to training_loss.png")