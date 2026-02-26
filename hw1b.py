import random

def simulate_step(y1, y2, y3):
    rate1 = 0.5 * y1 * (y1 - 1) * y2
    rate2 = y1 * y3 * (y3 - 1)
    rate3 = 3.0 * y2 * y3
    total_rate = rate1 + rate2 + rate3

    rand_val = random.random() * total_rate

    if rand_val < rate1:
        return y1 - 2, y2 - 1, y3 + 4
    elif rand_val < rate1 + rate2:
        return y1 - 1, y2 + 3, y3 - 2
    else:
        return y1 + 2, y2 - 1, y3 - 1


def run_simulation(iterations=200000, random_seed=1):
    random.seed(random_seed)

    values1 = []
    values2 = []
    values3 = []

    for _ in range(iterations):
        y1, y2, y3 = 9, 8, 7

        for _ in range(7):
            y1, y2, y3 = simulate_step(y1, y2, y3)

        values1.append(y1)
        values2.append(y2)
        values3.append(y3)

    def compute_mean_variance(data):
        count = len(data)
        mean_value = sum(data) / count
        variance_value = sum((item - mean_value) ** 2 for item in data) / count
        return mean_value, variance_value

    mean1, var1 = compute_mean_variance(values1)
    mean2, var2 = compute_mean_variance(values2)
    mean3, var3 = compute_mean_variance(values3)

    print(f"E[X1]={mean1:.6f}, Var(X1)={var1:.6f}")
    print(f"E[X2]={mean2:.6f}, Var(X2)={var2:.6f}")
    print(f"E[X3]={mean3:.6f}, Var(X3)={var3:.6f}")


if __name__ == "__main__":
    run_simulation()