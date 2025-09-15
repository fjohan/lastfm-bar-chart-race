# Last.fm Top Artists Aggregator  

This script fetches your listening history from [Last.fm](https://www.last.fm/) and builds a cumulative ranking of your **top 20 artists** over time.  
You can aggregate results **per month** or **per week**, and the output is saved to a CSV file for further analysis or visualization.  

---

## Features  
- Fetches listening history (scrobbles) from Last.fm using their public API.  
- Aggregates artist frequencies **cumulatively** over time.  
- Supports both **monthly** and **weekly** aggregation.  
- Prints the **top 5 artists** for each period to the console.  
- Writes the **top 20 artists** for each period to a CSV file.  
- Groups multiple artist names into one (e.g., solo vs. band names).  
- Fetches each artist’s **top tag** from Last.fm (used as category, e.g., "rock", "reggae") and caches it locally.  
- Uses caching to avoid refetching data or categories that were already retrieved.  

---

## Requirements  
- Python 3.8+  
- Packages:  
  ```bash
  pip install requests pandas


