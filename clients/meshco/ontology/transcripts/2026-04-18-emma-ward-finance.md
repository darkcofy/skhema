# Emma Ward — Head of Finance Systems — 2026-04-18

**Me:** Tell me about the close.

**Emma:** Monthly close. Five business days after month-end we have to sign
off the numbers. Right now it's 60% manual — we pull extracts from the
warehouse, reconcile against SAP, chase errors, post journals.

**Me:** What would change if you had SLO-backed data products?

**Emma:** If I could trust that orders gold is complete and accurate by day
+1, I can automate probably 30 of those 60 hours of manual work. The
blocker today is that I can't tell if the data is late, missing, or wrong
without comparing.

**Me:** What data products would the close depend on?

**Emma:** Orders, shipments, customer, product. Plus a finance-specific
product that takes orders + shipments + returns and gives us recognised
revenue per period.

**Me:** What's the SLO you'd want?

**Emma:** Completeness is the big one. "100% of orders in the period are
present in gold by day +1 9am UTC." Freshness matters but completeness is
where we get burned — we used to miss transactions because a batch silently
failed overnight.

**Me:** Reverse ETL — is that relevant for you?

**Emma:** Yes, huge. Currently once we finalise the month's numbers we
manually re-post customer lifetime value and cohort metrics back into SAP
for management reporting. If the platform can push that back automatically
after close, that's another six hours I save.

**Me:** Any data products you'd want to produce?

**Emma:** Finance produces the `finance.recognised_revenue` product.
Daily. Gold-tier. Consumers are management reporting, sales compensation,
and investor reporting.

**Me:** Push-back — does every team at MeshCo understand what a data
product is?

**Emma:** No. The engineering teams do, partly. Finance does because I've
been pushing it. Marketing and merchandising don't — they think "data
product" means something their data team makes for them. That's a comms
problem for the engagement.
