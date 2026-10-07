# AI Analysis Workflow

## 1. Data Understanding

**Prompt**

> List all the columns in the attached spreadsheet and show me a sample of data from each column.

**Follow-up**

> Take 5 more random samples of the data for each column to make sure you understand the format and type of information in each column.


## 2. Data Quality Assessment

**Prompt**

> Run a data quality check on each column. Specifically look for:
> 1. Missing, null, or empty values
> 2. Unexpected formats or data types
> 3. Outliers or suspicious values
> 4. Duplicated rows


## 3. Investigating Negative Prices

**Prompt**

> List rows with negative price values.

**Follow-up**

> Regarding A563186 and A563187, both have the description "Adjust bad debt" and a price of -11062.06. How should these records be interpreted and handled?

**Decision**

The records were treated as accounting adjustments outside the scope of retail sales analysis and excluded.


## 4. Analytical Question Setup

**Prompt**

> Tell me 10 interesting questions we could answer with this dataset and explain why each would be valuable.

**Follow-up**

> For questions 1, 2, and 3, tell me exactly which columns are needed and whether the current data is sufficient to answer them.


## 5. Changing the Spike Analysis

**Initial analysis**

AI examined gross sales, returns/cancellations, and net sales.

**My follow-up**

> Study net-sales spikes, since some gross-sales spikes occur together with returns/cancellation spikes.

**Decision**

Net sales was used to identify major positive sales events.


## 6. Market and Product Drill-Down

**Prompt**

> Explore the Top 20 net-sales spike dates by country.

**Follow-up**

> Separate UK and non-UK transactions and identify the products contributing to the spikes.


## 7. Return/Cancellation Analysis

**Prompt**

> What drove the largest return/cancellation spike? Study countries first, UK vs non-UK.

**Follow-up**

> Decompose the Top 10 return/cancellation dates by the Top 5 products for UK and non-UK separately.

