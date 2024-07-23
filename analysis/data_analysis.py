# analysis/data_analysis.py

import pandas as pd
import matplotlib.pyplot as plt


def analyze_data():
    data = pd.read_csv('../data.csv')
    # print(data.head())

    grouped_data = data.groupby('site').sum().reset_index()

    print(grouped_data)

    plt.figure(figsize=(10, 6))
    plt.bar(grouped_data['site'], grouped_data['download'], label='Download')
    plt.bar(grouped_data['site'], grouped_data['download_more'], bottom=grouped_data['download'], label='Download More')
    plt.xlabel('Site')
    plt.ylabel('Count')
    plt.title('Downloads by Site')
    plt.legend()
    plt.show()


if __name__ == "__main__":
    analyze_data()
