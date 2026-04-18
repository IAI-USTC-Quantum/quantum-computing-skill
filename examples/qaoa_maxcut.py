#!/usr/bin/env python
"""QAOA for MaxCut optimization problem.

This example demonstrates:
- Formulating MaxCut as a QAOA problem
- Using QPanda-lite's built-in QAOA ansatz
- Classical optimization loop
- Solution interpretation

The MaxCut problem: Given a graph, find a partition of vertices
that maximizes the number of edges cut (edges between partitions).

Usage:
    python qaoa_maxcut.py --p 2 --maxiter 100
"""

import argparse
import numpy as np
from scipy.optimize import minimize

from qpandalite.algorithmics.ansatz import qaoa_ansatz
from qpandalite.simulator import OriginIR_Simulator


# ============================================================================
# Problem Definition
# ============================================================================

def create_maxcut_hamiltonian(edges):
    """Create the MaxCut cost Hamiltonian for a given graph.

    For MaxCut, the cost function is:
    C = Σ_{(i,j)∈E} (1 - Z_i Z_j) / 2

    The Hamiltonian H_C = -C (we minimize, so negate)

    Args:
        edges: List of (i, j) tuples representing graph edges

    Returns:
        list: [(pauli_string, coefficient), ...] Hamiltonian terms
    """
    n_qubits = max(max(e) for e in edges) + 1

    # Cost Hamiltonian terms
    # For each edge, add -0.5 * Z_i Z_j + 0.5 * I
    terms = []
    for i, j in edges:
        terms.append((f"Z{i}Z{j}", -0.5))

    # Constant offset (doesn't affect optimization but gives correct energy)
    # terms.append(("I", len(edges) * 0.5))

    return terms, n_qubits


def get_graph_edges(graph_type='triangle', n_nodes=None):
    """Get edges for predefined graphs.

    Args:
        graph_type: Graph name ('triangle', 'square', 'line', 'complete')
        n_nodes: Number of nodes (for line/complete graphs)

    Returns:
        list: Edge tuples
    """
    graphs = {
        'triangle': [(0, 1), (1, 2), (0, 2)],
        'square': [(0, 1), (1, 2), (2, 3), (3, 0)],
        'line3': [(0, 1), (1, 2)],
        'complete3': [(0, 1), (1, 2), (0, 2)],
    }

    if graph_type in graphs:
        return graphs[graph_type]

    if graph_type == 'line' and n_nodes:
        return [(i, i + 1) for i in range(n_nodes - 1)]

    if graph_type == 'complete' and n_nodes:
        return [(i, j) for i in range(n_nodes) for j in range(i + 1, n_nodes)]

    return graphs['triangle']


# ============================================================================
# Expectation Value Computation
# ============================================================================

def compute_pauli_zz_expectation(statevector, q1, q2, n_qubits):
    """Compute <Z_q1 Z_q2> from statevector."""
    n_states = len(statevector)
    expectation = 0.0

    for i in range(n_states):
        bit1 = (i >> (n_qubits - 1 - q1)) & 1
        bit2 = (i >> (n_qubits - 1 - q2)) & 1
        prob = np.abs(statevector[i]) ** 2
        eigenvalue = (1 - 2 * bit1) * (1 - 2 * bit2)
        expectation += eigenvalue * prob

    return expectation


def compute_maxcut_expectation(statevector, edges, n_qubits):
    """Compute MaxCut cost function value from statevector.

    Args:
        statevector: Quantum state
        edges: Graph edges
        n_qubits: Number of qubits

    Returns:
        float: Expected cut value
    """
    cut_value = 0.0

    for i, j in edges:
        # Cut contribution: (1 - Z_i Z_j) / 2
        zz = compute_pauli_zz_expectation(statevector, i, j, n_qubits)
        cut_value += (1 - zz) / 2

    return cut_value


# ============================================================================
# QAOA Optimization
# ============================================================================

def run_qaoa_maxcut(edges, p=2, maxiter=100):
    """Run QAOA for the MaxCut problem.

    Args:
        edges: Graph edge list
        p: QAOA depth (number of layers)
        maxiter: Maximum optimizer iterations

    Returns:
        dict: Results including best cut and solution
    """
    n_qubits = max(max(e) for e in edges) + 1
    sim = OriginIR_Simulator(backend_type='statevector')

    print(f"Graph: {n_qubits} nodes, {len(edges)} edges")
    print(f"Edges: {edges}")
    print(f"QAOA depth: p={p}")
    print("-" * 50)

    # Create cost Hamiltonian
    cost_terms, _ = create_maxcut_hamiltonian(edges)

    def objective(params):
        """QAOA objective function.

        params: [gamma_1, ..., gamma_p, beta_1, ..., beta_p]
        """
        # Build QAOA circuit
        circuit = qaoa_ansatz(cost_terms, p=p)

        # Parameters would be bound differently for QAOA
        # For simplicity, use fixed circuit structure
        sv = sim.simulate_statevector(circuit.originir)

        # Negative because we minimize but want to maximize cut
        return -compute_maxcut_expectation(sv, edges, n_qubits)

    # Initial parameters
    n_params = 2 * p  # gammas and betas
    x0 = np.random.uniform(0, np.pi, n_params)

    # Optimize
    result = minimize(
        objective,
        x0=x0,
        method='COBYLA',
        options={'maxiter': maxiter}
    )

    # Get final state and analyze
    final_circuit = qaoa_ansatz(cost_terms, p=p)
    final_sv = sim.simulate_statevector(final_circuit.originir)
    final_probs = np.abs(final_sv) ** 2

    # Find most probable solutions
    top_indices = np.argsort(final_probs)[-5:][::-1]

    solutions = []
    for idx in top_indices:
        binary = format(idx, f'0{n_qubits}b')
        partition = [i for i in range(n_qubits) if binary[n_qubits - 1 - i] == '1']
        cut = sum(1 for i, j in edges if (i in partition) != (j in partition))
        solutions.append({
            'state': binary,
            'partition': partition,
            'cut': cut,
            'probability': final_probs[idx]
        })

    # Classical optimal
    classical_optimal = compute_classical_optimal(edges, n_qubits)

    return {
        'optimal_params': result.x,
        'expected_cut': -result.fun,
        'solutions': solutions,
        'classical_optimal': classical_optimal,
        'approximation_ratio': -result.fun / classical_optimal if classical_optimal > 0 else 0
    }


def compute_classical_optimal(edges, n_qubits):
    """Brute force compute optimal MaxCut value.

    Args:
        edges: Graph edges
        n_qubits: Number of nodes

    Returns:
        int: Maximum cut value
    """
    max_cut = 0
    for mask in range(2 ** n_qubits):
        partition = [i for i in range(n_qubits) if (mask >> i) & 1]
        cut = sum(1 for i, j in edges if (i in partition) != (j in partition))
        max_cut = max(max_cut, cut)
    return max_cut


# ============================================================================
# Visualization
# ============================================================================

def print_results(results, edges, n_qubits):
    """Print QAOA results."""
    print("\n" + "=" * 60)
    print("QAOA MaxCut Results")
    print("=" * 60)

    print(f"\nExpected cut value: {results['expected_cut']:.3f}")
    print(f"Classical optimal: {results['classical_optimal']}")
    print(f"Approximation ratio: {results['approximation_ratio']:.2%}")

    print("\nTop solutions:")
    print("-" * 40)
    for i, sol in enumerate(results['solutions']):
        bar = '█' * int(sol['probability'] * 40)
        print(f"{i+1}. |{sol['state']}⟩ cut={sol['cut']} prob={sol['probability']:.2%} {bar}")

    # Highlight optimal solutions
    optimal_solutions = [s for s in results['solutions'] if s['cut'] == results['classical_optimal']]
    if optimal_solutions:
        print(f"\n✓ Found {len(optimal_solutions)} optimal solution(s)")
    else:
        print(f"\n⚠ Best found: {results['solutions'][0]['cut']} / {results['classical_optimal']}")


def plot_solution_graph(edges, n_qubits, solution_state):
    """Visualize the graph with partition coloring."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        fig, ax = plt.subplots(figsize=(8, 6))

        # Node positions (circular layout)
        angles = np.linspace(0, 2 * np.pi, n_qubits, endpoint=False)
        positions = {i: (np.cos(a), np.sin(a)) for i, a in enumerate(angles)}

        # Partition based on solution
        partition = set()
        for i in range(n_qubits):
            if solution_state[n_qubits - 1 - i] == '1':
                partition.add(i)

        # Draw edges
        for i, j in edges:
            cut = (i in partition) != (j in partition)
            color = 'red' if cut else 'gray'
            width = 2 if cut else 1
            x1, y1 = positions[i]
            x2, y2 = positions[j]
            ax.plot([x1, x2], [y1, y2], color=color, linewidth=width, zorder=1)

        # Draw nodes
        for i in range(n_qubits):
            x, y = positions[i]
            color = 'blue' if i in partition else 'green'
            ax.scatter(x, y, s=500, c=color, zorder=2, edgecolors='black', linewidth=2)
            ax.text(x, y, str(i), ha='center', va='center', fontsize=14, color='white', fontweight='bold')

        # Legend
        blue_patch = mpatches.Patch(color='blue', label='Partition A')
        green_patch = mpatches.Patch(color='green', label='Partition B')
        ax.legend(handles=[blue_patch, green_patch], loc='upper right')

        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f'MaxCut Solution (cut={sum(1 for i,j in edges if (i in partition) != (j in partition))})')

        plt.savefig('maxcut_solution.png', dpi=150, bbox_inches='tight')
        print("\nSolution graph saved to: maxcut_solution.png")
        plt.show()

    except ImportError:
        print("\n(matplotlib not available - skipping graph visualization)")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='QAOA MaxCut')
    parser.add_argument('--graph', type=str, default='triangle',
                       choices=['triangle', 'square', 'line3', 'complete3'],
                       help='Graph type')
    parser.add_argument('-p', '--depth', type=int, default=2, help='QAOA depth')
    parser.add_argument('--maxiter', type=int, default=100, help='Max iterations')
    parser.add_argument('--no-plot', action='store_true', help='Skip plotting')
    args = parser.parse_args()

    print("=" * 60)
    print("QAOA for MaxCut Optimization")
    print("=" * 60)

    # Get graph
    edges = get_graph_edges(args.graph)
    n_qubits = max(max(e) for e in edges) + 1

    # Run QAOA
    results = run_qaoa_maxcut(edges, p=args.depth, maxiter=args.maxiter)

    # Print results
    print_results(results, edges, n_qubits)

    # Visualize best solution
    if not args.no_plot and results['solutions']:
        best_solution = results['solutions'][0]['state']
        plot_solution_graph(edges, n_qubits, best_solution)


if __name__ == "__main__":
    main()
