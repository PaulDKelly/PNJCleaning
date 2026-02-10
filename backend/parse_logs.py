import json

try:
    log_lines = []
    with open('raw_logs.json', 'r', encoding='utf-16-le') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    start = line.find('{')
                    end = line.rfind('}')
                    if start != -1 and end != -1:
                        data = json.loads(line[start:end+1])
                        log_lines.append(data.get('Log', '').strip())
                except:
                    pass

    with open('parsed_traceback.txt', 'w', encoding='utf-8') as out:
        # Find all instances of callback_failed
        for i, line in enumerate(log_lines):
            if 'callback_failed' in line:
                out.write(f"--- Found failure at line {i} ---\n")
                # Print 50 lines before to be safe
                start_idx = max(0, i - 50)
                for j in range(start_idx, i + 1):
                    out.write(f"{j}: {log_lines[j]}\n")
                out.write("\n")
    print("Wrote results to parsed_traceback.txt")
except Exception as e:
    print(f"Error: {e}")
