



Tips: use matplotlib, seaborn, or visuzlization tools of your choice.




######

# Smoke Test Analysis & Comparison Framework

Develop a lightweight, extensible, and automated toolkit designed to ingest, parse, and visualize smoke test execution results. 
This framework helps engineering teams quickly identify performance regressions, compare test durations, and track metrics across 
multiple execution runs.

Note you are explicity allowed to use any LLM service you like.
Please note that you still have to verify its correctness. You can collaborate with or leverage other peoples ideas as long as you acknowledge.

---

## 📂 Repository Structure

User 

username ::= The username that is in your ~/.config/cloudmesh/clouds.yaml file 

```yaml
couds:
    ...
    username: ...
```

```text
├── results/                   # Place your raw smoke test result files (.json or .csv) here
└── <username>/
    ├── images                 # Place all your images here
    ├── comparison.md         # Place all your images here
    ├── analyze-smoke-tests.py # Core analysis and visualization script
    ├── analyze-smoke-notebook.ipynb # Core analysis and visualization script
    ├── requirements.txt       # Python dependencies
    ├── ai-ussage.md       # Documentation on AI-assisted development workflow
    ├── Makefile               # Create a usable makefile
    └── acknowledgement.md    # Project attributions and references

```

You are allowed to use jupyter notebook or plain python. In case of jupyter you can also use paperpile.

---

### 4. Run the Analysis Script

Execute the script to parse the result files and automatically generate a high-resolution comparison document including all images

---

## Key Features

- **Multi-Format Ingestion:** Automatically detects, reads, and merges both JSON and CSV test outputs from the results directory.
- **Dynamic Plotting:** Uses `seaborn`, `matplotlib` or others to render clean, readable comparative bar charts highlighting execution times or test performance metrics.
