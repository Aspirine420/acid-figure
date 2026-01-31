🧠 Neuro-Arena: Neural Network Evolution Simulator
A high-speed autonomous AI battle simulation built with Python, Pygame, and NumPy. Two competing teams of neural-network-driven agents evolve in real-time to master a complex "Capture the Flag" environment.
🚀 Overview
Each agent in this simulation is powered by a custom shallow neural network (Brain). There is no hardcoded pathfinding; agents must learn to navigate, manage resources, and engage in combat through a continuous Genetic Algorithm.
🧬 Key Features
Neural Intelligence: Every unit uses a 12-input, 2-layer MLP (Multi-Layer Perceptron) to process environmental data into movement and rotation.
Evolutionary Learning: When a unit dies, its weights are mutated and passed to a new spawn. Successful traits (like dodging or resource gathering) naturally dominate the gene pool over time.
Dynamic Roles: The simulation assigns roles—LEADERS focus on flags, SUPPLIERS hunt for resources, and DEFENDERS protect the base.
Veteran System: Units that survive longer than 120 seconds gain "Veteran" status, increasing their damage and tactical efficiency.
Live Debugging: Click on any unit to see its real-time thought process, inventory, and a visualization of its neural weight activations.
🕹 Game Mechanics
🏁 Capture the Flag: The primary goal. Stealing the enemy flag and returning it to base grants massive score bonuses.
🔋 Metabolism: Moving and shooting costs energy. Units must find "Food" (yellow circles) or "Energy Cells" (blue) to survive.
⚔️ Arsenal:
Pistol: Standard issue.
Shotgun: High spread, high damage (cyan crates).
Sniper: Long range, piercing damage (purple triangles).
🛡 Boss Units: Each team has a "Mega-Boss" with high HP and multi-shot capabilities to act as a tactical anchor.
🛠 Installation & Usage
Requirements:
bash
pip install pygame numpy
Используйте код с осторожностью.

Run Simulation:
bash
python neuro_arena.py
Используйте код с осторожностью.

📊 Neural Input Mapping
The agents "see" the world through 11 specific inputs, including:
Relative Enemy Pos: (X, Y)
Target Vector: Direction to flag or resource.
Internal State: HP ratio, Energy levels, Ammo count.
Field Dominance: A global variable representing which team currently has more units.

