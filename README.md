# Automagic MzML Integrator!

This is a small script utilizing PyOpenMS to automatically integrate specific ion traces from LC-MS experiments.

- If you don't have it already, please follow the [PyOpenMS installation guide](https://pyopenms.readthedocs.io/en/latest/user_guide/installation.html). 

## Configuration

- Before opening, ensure that a folder named `data` is placed next to the `run.py` file. The `data` folder is where you can put all your MzML files.

<img width="367" height="355" alt="image" src="https://github.com/user-attachments/assets/37f60d53-904a-4b38-97aa-36b585a93587" />

- **Specify your search parameters** by editing `search_sheet.tsv`. `peak_name` is the label given to the integration result in the output. `detector` can be set to either FT or IT. If FT, `precursor` can be set to any value, as it is not used. Searches against the IT detector will expect a `precursor` to be set, and this is expected to be an exact match to a single precursor ion. `mz_start` and `mz_end` specify the m/z range for the ion trace. These can be arbitrarily wide (0 to 99999) for a TIC chromatogram. `rt_start` and `rt_end` are the LC retention times (in seconds) to integrate between.

<img width="874" height="404" alt="image" src="https://github.com/user-attachments/assets/bb4d583e-7b23-472a-a6e7-57d4b4dd5ad3" />

## Usage

- Double-click `run.py` to open the GUI. This will list your MzML files.

<img width="455" height="508" alt="image" src="https://github.com/user-attachments/assets/fbe35db1-0b93-4f75-80a2-787876b40c7e" />


- 'Verbose' will print extra information to the console. This is probably not needed.
- 'Save Images' will save a .jpg file for each of the integrations performed. This generates a very large number of image files: One image per search, per file.

Select one or multiple files and click "Run selected" to perform searches on these files. Click "Run all" to perform searches on all files. Searching will cause the GUI to freeze, this is because I did not put the actual processing on another thread. You can verify that the program is working by inspecting the associated cmd window.

- The output for all searches will be placed in `results.tsv`.
