import re
# import matplotlib.pyplot as plt

def position_sizing(cash, last_price, cash_at_risk):
    if last_price is None:
        print("Error: Last price is not available.")

    if cash <=0:
        print("Error: Insufficient cash available for trading.")

    quantity = round(cash * cash_at_risk / last_price, 0)

    if quantity <=0:
        print("Error: Calculated quantity is not positive.")
    return quantity


def symbol_type(symbol:str):
    if re.search(r'\d', symbol):
        raise argparse.ArgumentTypeError("Symbol must not contain any digits")
    return symbol.upper()

# def moving_avg_plots(data, short_window, long_window, nbr):
#     prices = data[0]
#     short_ma = data[1]
#     long_ma = data[2]
#     plt.figure(figsize=(10, 6))
#     plt.plot(prices, label='Prices', color='blue')
#     plt.plot(short_ma, label=f'Short MA ({short_window})', color='orange')
#     plt.plot(long_ma, label=f'Long MA ({long_window})', color='green')
#     plt.title('Moving Averages')
#     plt.xlabel('Time')
#     plt.ylabel('Value')
#     plt.legend()
#     plt.grid(True)

#     # Save the plot as HTML file
#     plt.savefig(f'moving_averages_plot_{nbr}.png')
