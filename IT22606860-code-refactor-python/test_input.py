def process_data(data):
    results = []
    for i in range(len(data)):
        if data[i] > 0:
            if data[i] < 100:
                results.append(data[i] * 2)
    unused_var = 42
    if len(results) > 5:
        return results[:5]
    else:
        return results
