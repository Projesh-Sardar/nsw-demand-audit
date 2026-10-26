# What the data can't tell you: an audit of NSW electricity demand and temperature

A data quality audit of two public time series, and an honest account of what
they can and cannot support.

## Why this exists

Electricity demand in NSW rises on hot days and on cold days, and falls in
between. It is one of the cleanest non-linear relationships in any public
Australian dataset, and it is lagged — a run of hot nights matters more than a
single hot afternoon.

Before any of that can be modelled, someone has to find out whether the data is
sound. That is what this project does. The modelling is deliberately the last
and smallest part.

## The datasets

**Temperature** — Open-Meteo historical archive. Free, no API key, daily values
back to 1940. `get_weather.py` pulls it.

**Electricity demand** — AEMO aggregated price and demand data, half-hourly by
region, published as monthly CSVs:
https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/aggregated-data

Download NSW1 for the years you want and put the CSVs in `data/`. The timestamp
column is `SETTLEMENTDATE` and demand is `TOTALDEMAND`.

## Running it

```bash
pip install pandas requests
python get_weather.py 2015-01-01 2024-12-31
python audit.py data/weather_sydney.csv date
python audit.py data/demand_nsw.csv SETTLEMENTDATE
```

## What the audit checks, and why each one matters

| Check | The question | Why it matters |
|---|---|---|
| Gaps | Are time steps missing entirely? | A missing row and a row with a missing value are different things, and most code treats them differently without telling you |
| Duplicates | Is a timestamp repeated? | In Australian data this is usually the April daylight saving rollback, where 2am happens twice |
| Missing values | Where are the nulls, and are they clustered? | Clustered nulls mean something broke for a period; scattered nulls mean something else. Different problems, different treatment |
| Outliers | Values far outside the usual range | Some are sentinel codes standing in for "missing". Some are the most interesting real events in the dataset. You have to look to know which |
| Flatlines | Runs of identical values | A failed sensor often keeps reporting its last reading. That looks like data and isn't |
| Year-on-year stability | Does the series behave the same way throughout? | A jump in mean or variance between years usually means a definitional change or a new instrument, not a change in the world |

The last one is the check most people skip and the one most likely to find
something real. For NSW demand specifically: rooftop solar has grown enormously
over the past decade, and it reduces *measured* demand without reducing actual
electricity use. A naive model fitted across ten years will read that as
falling demand. It isn't.

## What to write up

Three sections. Roughly a thousand words in total, and the second is the one
that matters.

**1. What I found.** Each problem, what it is, and what you think caused it.
Show the evidence.

**2. What this data cannot answer.** The honest limits. If rooftop solar makes
pre-2018 and post-2018 demand non-comparable, say so and say why. If the
temperature series is a modelled grid cell rather than a weather station — and
it is — say what that means for a city with a coastline.

**3. What I would need.** What extra data, or what different approach, would be
required to answer the question properly.

Only after that, if you want: plot demand against temperature and show the
U-shape. One chart. It is the reward, not the point.

## What "done" looks like

- The audit runs on both datasets and the output is saved
- The write-up exists and is honest about limits
- A README someone else could follow to reproduce it
- It is on GitHub, public, with your name on it

Not: a dashboard, a model with impressive accuracy, or a web interface. Those
would all be more impressive and less useful, because you could not defend
every decision in them.

## The standard to hold yourself to

Every line of this should be something you can explain to someone who asks why.
If you cannot explain why a check is there, take it out. A short project you
understand completely is worth more than a large one you don't.
