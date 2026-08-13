import random
import statistics

# --- CONFIGURATION ---
NUM_QUERIES = 176               # Total number of search queries (equals 352 AIOs)
MAX_QUERIES_PER_USER = 5        # 5 queries per participant (equals 10 AIOs)
NUM_USERS = 71                  # The 71 participants from Prolific
GHOST_RATE = 0.0                # 0%, since Prolific automatically replaces drop-outs

def run_simulation():
    # Initialize all queries with 0 completed/active assessments
    # Format: { query_id: number_of_valid_assessments }
    live_scores = {i: 0 for i in range(1, NUM_QUERIES + 1)}
    
    ghost_count = 0
    success_count = 0

    print(f"Starting simulation with {NUM_USERS} users (Drop-out rate: {GHOST_RATE*100}%)...")

    for user_id in range(NUM_USERS):
        # 1. LIVE-SCORE SORTING
        # Sort queries by their current live score (least-reviewed first).
        # random.random() breaks ties randomly when scores are identical.
        sorted_queries = sorted(live_scores.keys(), key=lambda q: (live_scores[q], random.random()))
        
        # 2. ADAPTIVE CANDIDATE POOL (Our Top-N logic)
        # Select twice the amount of needed queries, capped safely at the total query count.
        pool_size = min(MAX_QUERIES_PER_USER * 2, NUM_QUERIES)
        candidate_pool = sorted_queries[:pool_size]
        
        # 3. RANDOM SAMPLING FROM THE POOL
        # Randomly pick the required queries from this high-priority candidate subset.
        # This breaks up the sequential presentation of related queries.
        chosen_queries = random.sample(candidate_pool, min(len(candidate_pool), MAX_QUERIES_PER_USER))
        
        # 4. SIMULATE USER BEHAVIOR
        # Determine if this simulated participant becomes a "ghost"
        is_ghost = random.random() < GHOST_RATE
        
        if is_ghost:
            # User drops out. In the real app, these records hold status=0 and expire after 45 minutes.
            # In this simulation, their drop-out simply means the live score does NOT increase.
            ghost_count += 1
        else:
            # User completes all tasks. Status updates to 1, and the query live score increases.
            success_count += 1
            for q in chosen_queries:
                live_scores[q] += 1

    # --- EVALUATION & STATISTICAL ANALYSIS ---
    print("\n" + "="*40)
    print("ALLOCATION SIMULATION RESULTS")
    print("="*40)
    print(f"Successful Participants: {success_count}")
    print(f"Ghost Participants:      {ghost_count}")
    print("-" * 40)
    
    # Display the final distribution visualization
    distribution = list(live_scores.values())
    for q_id, score in live_scores.items():
        bar = '█' * int(score / 2) if score > 0 else ''
        print(f"Query {q_id:02d}: {score} reviews {bar}")
        
    print("-" * 40)
    print(f"Lowest Review Count:  {min(distribution)}")
    print(f"Highest Review Count: {max(distribution)}")
    print(f"Maximum Deviation:    {max(distribution) - min(distribution)} reviews")
    
    # Calculate standard deviation to measure balancing quality
    std_dev = statistics.stdev(distribution)
    print(f"Standard Deviation:   {std_dev:.2f} (lower means more perfectly balanced)")

if __name__ == "__main__":
    run_simulation()