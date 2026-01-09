students = [
    {"name": "Alice", "score": 85},
    {"name": "Bob", "score": 72},
    {"name": "Charlie", "score": 90},
    {"name": "David", "score": 78}
]

import matplotlib.pyplot as plt

names = [student["name"] for student in students]
scores = [student ["score"] for student in students]

average_score = sum(scores) / len(scores)
print(f"Average score: {average_score}")

plt.figure()
plt.bar(names,scores)
plt.axhline(average_score, linestyle='--', color='r')
plt.xlabel("Students")
plt.ylabel("Scores")
plt.title("Student Test Scores")
plt.legend()
plt.show()