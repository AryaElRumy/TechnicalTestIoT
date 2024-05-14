import json
import pandas as pd

# Memuat data JSON
with open('voltage_data.json') as f:
    data = json.load(f)

# Membuat DataFrame dari data JSON
df = pd.DataFrame(data)

# Menyimpan DataFrame ke file CSV
df.to_csv('data_voltage.csv', index=False)