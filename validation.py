import pandas as pd
import matplotlib.pyplot as plt

# Read raw datasets
df_0910 = pd.read_csv("Retail 2009-10.csv", low_memory=False)
df_1011 = pd.read_csv("Retail 2010-11.csv", low_memory=False)


# Data quality check
def quality_check(df):

    results = []

    for column in df.columns:

        row = {
            "Column": column,
            "Data Type": str(df[column].dtype),
            "Missing": df[column].isna().sum(),
            "Missing %": round(df[column].isna().mean() * 100, 2),
            "Min": "-",
            "Max": "-",
            "Mean": "-",
            "Median": "-"
        }

        # Summary statistics for numeric columns
        if pd.api.types.is_numeric_dtype(df[column]):
            row["Min"] = round(df[column].min(), 2)
            row["Max"] = round(df[column].max(), 2)
            row["Mean"] = round(df[column].mean(), 2)
            row["Median"] = round(df[column].median(), 2)

        results.append(row)

    return pd.DataFrame(results)

quality_0910 = quality_check(df_0910)
quality_1011 = quality_check(df_1011)

print("\nRetail 2009-10")
print(quality_0910.to_string(index=False))

print("\nRetail 2010-11")
print(quality_1011.to_string(index=False))

# Combine two datasets
df = pd.concat(
    [df_0910, df_1011],
    ignore_index=True
)

print("\n--- Combined dataset ---")
print("Rows:", len(df))
print("Columns:", len(df.columns))

# Check duplicates

duplicate_count = df.duplicated().sum()

print("\n--- Duplicate check ---")
print("Duplicate rows:", duplicate_count)
print("Duplicate %:",round(duplicate_count / len(df) * 100, 2))

# Remove duplicates
df = df.drop_duplicates().copy()

print("\n--- After removing duplicates ---")
print("Rows:", len(df))
print("Remaining duplicates:", df.duplicated().sum())

# Remove zero and negative prices
df = df[df["Price"] > 0].copy()

print("\n--- After removing Price <= 0 ---")
print("Rows:", len(df))
print("Price <= 0:", (df["Price"] <= 0).sum())

# Convert InvoiceDate
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"],
    format="%d-%m-%Y %H:%M",
    errors="coerce"
)

print("\n--- Date validation ---")
print("Invalid dates:", df["InvoiceDate"].isna().sum())
print("Start date:", df["InvoiceDate"].min())
print("End date:", df["InvoiceDate"].max())
df["Date"] = df["InvoiceDate"].dt.normalize()# Create calendar date for daily analysis

# Calculate revenue
df["Revenue"] = df["Quantity"] * df["Price"]

# Revenue validation
gross_sales = df.loc[df["Quantity"] > 0, "Revenue"].sum()
returns_cancellations = df.loc[df["Quantity"] < 0,"Revenue"].sum()
net_sales = df["Revenue"].sum()

print("\n--- Revenue validation ---")
print("Gross sales:", round(gross_sales, 2))
print("Returns/cancellations:", round(returns_cancellations, 2))
print("Net sales:", round(net_sales, 2))
print("Gross + returns = net:", round(gross_sales + returns_cancellations, 2) == round(net_sales, 2))

# Daily sales revenue trend
# Aggregate daily revenue
daily_sales = (
    df.groupby("Date")
    .agg(
        Gross_Sales=(
            "Revenue",
            lambda x: x[df.loc[x.index, "Quantity"] > 0].sum()
        ),
        Returns_Cancellations=(
            "Revenue",
            lambda x: x[df.loc[x.index, "Quantity"] < 0].sum()
        ),
        Net_Sales=("Revenue", "sum")
    )
    .reset_index()
)

# Plot daily revenue trend
plt.figure(figsize=(14, 6))

plt.plot(
    daily_sales["Date"],
    daily_sales["Gross_Sales"],
    label="Gross Sales"
)

plt.plot(
    daily_sales["Date"],
    daily_sales["Returns_Cancellations"],
    label="Returns/Cancellations"
)

plt.plot(
    daily_sales["Date"],
    daily_sales["Net_Sales"],
    label="Net Sales"
)

plt.axhline(0, linewidth=0.8)

plt.title("Daily Sales Revenue Trend")
plt.xlabel("Invoice Date")
plt.ylabel("Revenue")
plt.legend()

plt.tight_layout()
plt.show()

# Top 20 net sales spikes by country
# Identify Top 20 dates with the highest net sales
top20_dates = (
    daily_sales
    .nlargest(20, "Net_Sales")
    [["Date", "Net_Sales"]]
)
print("\n--- Top 20 Net Sales Dates ---")
print(top20_dates.to_string(index=False))


# Calculate country contribution on Top 20 dates
top20_country = (
    df[df["Date"].isin(top20_dates["Date"])]
    .groupby(["Date", "Country"])["Revenue"]
    .sum()
    .unstack(fill_value=0)
)


# Keep dates in descending order of net sales
top20_country = (
    top20_country
    .reindex(top20_dates["Date"])
)


# Select Top 8 countries by total absolute contribution
top_countries = (
    top20_country
    .abs()
    .sum()
    .nlargest(8)
    .index
)

# Group remaining countries as Other
country_plot = top20_country[top_countries].copy()

country_plot["Other"] = (
    top20_country
    .drop(columns=top_countries)
    .sum(axis=1)
)

# Plot country contribution
country_plot.plot(
    kind="bar",
    stacked=True,
    figsize=(14, 7)
)

plt.title("Top 20 Net Sales Spikes by Country")
plt.xlabel("Invoice Date")
plt.ylabel("Net Sales")
plt.xticks(rotation=45, ha="right")
plt.legend(
    title="Country",
    bbox_to_anchor=(1.05, 1),
    loc="upper left"
)

plt.tight_layout()
plt.show()

# Top 5 products on Top 20 net sales spike dates
# UK vs Non-UK

# Filter Top 20 net sales dates
spike_data = df[
    df["Date"].isin(top20_dates["Date"])
].copy()


# Define UK and Non-UK markets
spike_data["Market"] = spike_data["Country"].apply(
    lambda x: "UK" if x == "United Kingdom" else "Non-UK"
)


# Function to plot Top 5 products + Other
def plot_top5_products(data, market):

    market_data = data[
        data["Market"] == market
    ].copy()

    # Identify Top 5 products by total net sales
    top5_codes = (
        market_data
        .groupby("StockCode")["Revenue"]
        .sum()
        .nlargest(5)
        .index
    )

    # Get product descriptions
    descriptions = (
        market_data[
            market_data["StockCode"].isin(top5_codes)
        ]
        .groupby("StockCode")["Description"]
        .first()
    )

    # Create readable product labels
    product_labels = {
        code: f"{code} — {descriptions[code]}"
        for code in top5_codes
    }

    # Top 5 products keep their labels;
    # all remaining products become Other
    market_data["Product"] = (
        market_data["StockCode"]
        .map(product_labels)
        .fillna("Other")
    )

    # Aggregate by date and product
    product_daily = (
        market_data
        .groupby(["Date", "Product"])["Revenue"]
        .sum()
        .unstack(fill_value=0)
        .reindex(top20_dates["Date"])
    )

    # Format dates as dd-mm-yyyy
    product_daily.index = (
        product_daily.index.strftime("%d-%m-%Y")
    )

    # Plot
    product_daily.plot(
        kind="bar",
        stacked=True,
        figsize=(14, 7)
    )

    plt.title(
        f"Top 20 Net Sales Spikes — {market} Top 5 Products"
    )
    plt.xlabel("Invoice Date")
    plt.ylabel("Net Sales")
    plt.xticks(rotation=45, ha="right")

    plt.legend(
        title="Product",
        bbox_to_anchor=(1.05, 1),
        loc="upper left"
    )

    plt.tight_layout()
    plt.show()


# UK
plot_top5_products(
    spike_data,
    "UK"
)

# Non-UK
plot_top5_products(
    spike_data,
    "Non-UK"
)

# Explore selected country spikes:
# Top 5 products + Other

country_dates = {
    "Australia": [
        "29-11-2010",
        "05-10-2011"
    ],
    
    "EIRE": [
        "07-01-2010"
    ],
    
    "Netherlands": [
        "29-11-2010",
        "23-11-2010",
        "07-12-2011",
        "11-08-2011",
        "29-03-2011"
    ]
}


def plot_country_top5_products(df, country, dates):

    # Convert selected dates to datetime
    selected_dates = pd.to_datetime(
        dates,
        format="%d-%m-%Y"
    )

    # Filter country and selected dates
    country_data = df[
        (df["Country"] == country) &
        (df["Date"].isin(selected_dates))
    ].copy()


    # Identify Top 5 products by total net sales
    top5_codes = (
        country_data
        .groupby("StockCode")["Revenue"]
        .sum()
        .nlargest(5)
        .index
    )

    # Get product descriptions
    descriptions = (
        country_data[
            country_data["StockCode"].isin(top5_codes)
        ]
        .groupby("StockCode")["Description"]
        .first()
    )

    # Create product labels
    product_labels = {
        code: f"{code} — {descriptions[code]}"
        for code in top5_codes
    }

    # Group all remaining products as Other
    country_data["Product"] = (
        country_data["StockCode"]
        .map(product_labels)
        .fillna("Other")
    )

    # Aggregate net sales by date and product
    product_daily = (
        country_data
        .groupby(["Date", "Product"])["Revenue"]
        .sum()
        .unstack(fill_value=0)
        .reindex(selected_dates, fill_value=0)
    )


    # Format dates as dd-mm-yyyy
    product_daily.index = (
        product_daily.index.strftime("%d-%m-%Y")
    )


    # Plot
    product_daily.plot(
        kind="bar",
        stacked=True,
        figsize=(12, 6)
    )

    plt.title(
        f"{country} Sales Spikes — Top 5 Products"
    )
    plt.xlabel("Invoice Date")
    plt.ylabel("Net Sales")
    plt.xticks(rotation=45, ha="right")

    plt.legend(
        title="Product",
        bbox_to_anchor=(1.05, 1),
        loc="upper left"
    )

    plt.tight_layout()
    plt.show()


# Australia
plot_country_top5_products(df, "Australia", country_dates["Australia"])

# EIRE
plot_country_top5_products(df, "EIRE", country_dates["EIRE"])

# Netherlands
plot_country_top5_products(df, "Netherlands", country_dates["Netherlands"])

# Top 10 return/cancellation spike dates

# Keep negative-quantity transactions
negative_data = df[
    df["Quantity"] < 0
].copy()

# Calculate daily return/cancellation value
daily_returns = (
    negative_data
    .groupby("Date")["Revenue"]
    .sum()
)

# Identify Top 10 largest negative spikes
top10_return_dates = (
    daily_returns
    .nsmallest(10)
)

print("\n--- Top 10 Return/Cancellation Dates ---")
print(top10_return_dates)

# Define UK and Non-UK

negative_data["Market"] = negative_data["Country"].apply(
    lambda x: "UK" if x == "United Kingdom" else "Non-UK"
)

return_spikes = negative_data[
    negative_data["Date"].isin(top10_return_dates.index)
].copy()

# UK return/cancellation spikes
uk_returns = (
    return_spikes[
        return_spikes["Market"] == "UK"
    ]
    .groupby(["Date", "Country"])["Revenue"]
    .sum()
    .unstack(fill_value=0)
    .reindex(top10_return_dates.index, fill_value=0)
)

uk_returns.index = uk_returns.index.strftime("%d-%m-%Y")

uk_returns.plot(
    kind="bar",
    stacked=True,
    figsize=(12, 6)
)

plt.title("Top 10 Return/Cancellation Spikes — UK")
plt.xlabel("Invoice Date")
plt.ylabel("Return/Cancellation Value")
plt.xticks(rotation=45, ha="right")
plt.legend(
    title="Country",
    bbox_to_anchor=(1.05, 1),
    loc="upper left"
)

plt.tight_layout()
plt.show()

# Non-UK return/cancellation spikes
nonuk_returns = (
    return_spikes[
        return_spikes["Market"] == "Non-UK"
    ]
    .groupby(["Date", "Country"])["Revenue"]
    .sum()
    .unstack(fill_value=0)
    .reindex(top10_return_dates.index, fill_value=0)
)

nonuk_returns.index = nonuk_returns.index.strftime("%d-%m-%Y")

nonuk_returns.plot(kind="bar", stacked=True, figsize=(12, 6))

plt.title("Top 10 Return/Cancellation Spikes — Non-UK")
plt.xlabel("Invoice Date")
plt.ylabel("Return/Cancellation Value")
plt.xticks(rotation=45, ha="right")
plt.legend(
    title="Country",
    bbox_to_anchor=(1.05, 1),
    loc="upper left"
)

plt.tight_layout()
plt.show()


# Top 5 products driving return/cancellation spikes
def plot_return_top5_products(data, market):

    market_data = data[
        data["Market"] == market
    ].copy()


    # Identify Top 5 products with the largest negative return/cancellation values
    top5_codes = (
        market_data
        .groupby("StockCode")["Revenue"]
        .sum()
        .nsmallest(5)
        .index
    )


    # Get product descriptions
    descriptions = (
        market_data[
            market_data["StockCode"].isin(top5_codes)
        ]
        .groupby("StockCode")["Description"]
        .first()
    )


    # Create readable product labels
    product_labels = {
        code: f"{code} — {descriptions[code]}"
        for code in top5_codes
    }


    # Group remaining products as Other
    market_data["Product"] = (
        market_data["StockCode"]
        .map(product_labels)
        .fillna("Other")
    )


    # Aggregate by date and product
    product_daily = (
        market_data
        .groupby(["Date", "Product"])["Revenue"]
        .sum()
        .unstack(fill_value=0)
        .reindex(top10_return_dates.index, fill_value=0)
    )
    
    # Format dates
    product_daily.index = (
        product_daily.index.strftime("%d-%m-%Y")
    )

    # Plot
    product_daily.plot(
        kind="bar",
        stacked=True,
        figsize=(14, 7)
    )

    plt.title(
        f"Top 10 Return/Cancellation Spikes — "
        f"{market} Top 5 Products"
    )

    plt.xlabel("Invoice Date")
    plt.ylabel("Return/Cancellation Value")
    plt.xticks(rotation=45, ha="right")

    plt.legend(
        title="Product",
        bbox_to_anchor=(1.05, 1),
        loc="upper left"
    )

    plt.tight_layout()
    plt.show()

# UK Top 5 products

plot_return_top5_products(return_spikes, "UK")

# Non-UK Top 5 products
plot_return_top5_products(return_spikes, "Non-UK")
































































